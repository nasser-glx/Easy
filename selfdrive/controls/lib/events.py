from enum import IntEnum
from typing import Dict, Union, Callable, Any

from cereal import log, car
import cereal.messaging as messaging
from common.realtime import DT_CTRL
from selfdrive.config import Conversions as CV
from selfdrive.locationd.calibrationd import MIN_SPEED_FILTER

AlertSize = log.ControlsState.AlertSize
AlertStatus = log.ControlsState.AlertStatus
VisualAlert = car.CarControl.HUDControl.VisualAlert
AudibleAlert = car.CarControl.HUDControl.AudibleAlert
EventName = car.CarEvent.EventName


# Alert priorities
class Priority(IntEnum):
  LOWEST = 0
  LOWER = 1
  LOW = 2
  MID = 3
  HIGH = 4
  HIGHEST = 5


# Event types
class ET:
  ENABLE = 'enable'
  PRE_ENABLE = 'preEnable'
  NO_ENTRY = 'noEntry'
  WARNING = 'warning'
  USER_DISABLE = 'userDisable'
  SOFT_DISABLE = 'softDisable'
  IMMEDIATE_DISABLE = 'immediateDisable'
  PERMANENT = 'permanent'


# get event name from enum
EVENT_NAME = {v: k for k, v in EventName.schema.enumerants.items()}


class Events:
  def __init__(self):
    self.events = []
    self.static_events = []
    self.events_prev = dict.fromkeys(EVENTS.keys(), 0)

  @property
  def names(self):
    return self.events

  def __len__(self):
    return len(self.events)

  def add(self, event_name, static=False):
    if static:
      self.static_events.append(event_name)
    self.events.append(event_name)

  def clear(self):
    self.events_prev = {k: (v + 1 if k in self.events else 0) for k, v in self.events_prev.items()}
    self.events = self.static_events.copy()

  def any(self, event_type):
    for e in self.events:
      if event_type in EVENTS.get(e, {}).keys():
        return True
    return False

  def create_alerts(self, event_types, callback_args=None):
    if callback_args is None:
      callback_args = []

    ret = []
    for e in self.events:
      types = EVENTS[e].keys()
      for et in event_types:
        if et in types:
          alert = EVENTS[e][et]
          if not isinstance(alert, Alert):
            alert = alert(*callback_args)

          if DT_CTRL * (self.events_prev[e] + 1) >= alert.creation_delay:
            alert.alert_type = f"{EVENT_NAME[e]}/{et}"
            alert.event_type = et
            ret.append(alert)
    return ret

  def add_from_msg(self, events):
    for e in events:
      self.events.append(e.name.raw)

  def to_msg(self):
    ret = []
    for event_name in self.events:
      event = car.CarEvent.new_message()
      event.name = event_name
      for event_type in EVENTS.get(event_name, {}).keys():
        setattr(event, event_type, True)
      ret.append(event)
    return ret

# 메세지 한글화 : 로웰 ( https://github.com/crwusiz/openpilot )

class Alert:
  def __init__(self,
               alert_text_1: str,
               alert_text_2: str,
               alert_status: log.ControlsState.AlertStatus,
               alert_size: log.ControlsState.AlertSize,
               alert_priority: Priority,
               visual_alert: car.CarControl.HUDControl.VisualAlert,
               audible_alert: car.CarControl.HUDControl.AudibleAlert,
               duration_sound: float,
               duration_hud_alert: float,
               duration_text: float,
               alert_rate: float = 0.,
               creation_delay: float = 0.):

    self.alert_text_1 = alert_text_1
    self.alert_text_2 = alert_text_2
    self.alert_status = alert_status
    self.alert_size = alert_size
    self.alert_priority = alert_priority
    self.visual_alert = visual_alert
    self.audible_alert = audible_alert

    self.duration_sound = duration_sound
    self.duration_hud_alert = duration_hud_alert
    self.duration_text = duration_text

    self.alert_rate = alert_rate
    self.creation_delay = creation_delay

    self.start_time = 0.
    self.alert_type = ""
    self.event_type = None

  def __str__(self) -> str:
    return f"{self.alert_text_1}/{self.alert_text_2} {self.alert_priority} {self.visual_alert} {self.audible_alert}"

  def __gt__(self, alert2) -> bool:
    return self.alert_priority > alert2.alert_priority


class NoEntryAlert(Alert):
  def __init__(self, alert_text_2, audible_alert=AudibleAlert.chimeError, duration_sound=.4,
               visual_alert=VisualAlert.none, duration_hud_alert=2.):
    #super().__init__("openpilot Unavailable", alert_text_2, AlertStatus.normal,
    super().__init__("أوبن بايلوت غير متوفر", alert_text_2, AlertStatus.normal,
                     AlertSize.mid, Priority.LOW, visual_alert,
                     audible_alert, duration_sound, duration_hud_alert, 3.)


class SoftDisableAlert(Alert):
  def __init__(self, alert_text_2):
    #super().__init__("TAKE CONTROL IMMEDIATELY", alert_text_2,
    super().__init__("قم بالتحكم على الفور", alert_text_2,
                     AlertStatus.critical, AlertSize.full,
                     Priority.MID, VisualAlert.steerRequired,
                     AudibleAlert.chimeWarningRepeat, .1, 2., 2.),


class ImmediateDisableAlert(Alert):
  #def __init__(self, alert_text_2, alert_text_1="TAKE CONTROL IMMEDIATELY"):
  def __init__(self, alert_text_2, alert_text_1="قم بالتحكم على الفور"):
    super().__init__(alert_text_1, alert_text_2,
                     AlertStatus.critical, AlertSize.full,
                     Priority.HIGHEST, VisualAlert.steerRequired,
                     AudibleAlert.chimeWarningRepeat, 2.2, 3., 4.),


class EngagementAlert(Alert):
  def __init__(self, audible_alert=True):
    super().__init__("", "",
                     AlertStatus.normal, AlertSize.none,
                     Priority.MID, VisualAlert.none,
                     audible_alert, .2, 0., 0.),


class NormalPermanentAlert(Alert):
  def __init__(self, alert_text_1: str, alert_text_2: str, duration_text: float = 0.2):
    super().__init__(alert_text_1, alert_text_2,
                     AlertStatus.normal, AlertSize.mid if len(alert_text_2) else AlertSize.small,
                     Priority.LOWER, VisualAlert.none, AudibleAlert.none, 0., 0., duration_text),


# ********** alert callback functions **********
def below_steer_speed_alert(CP: car.CarParams, sm: messaging.SubMaster, metric: bool) -> Alert:
  speed = int(round(CP.minSteerSpeed * (CV.MS_TO_KPH if metric else CV.MS_TO_MPH)))
  unit = "كلم/س" if metric else "ميل"
  return Alert(
    #"TAKE CONTROL",
    #"Steer Unavailable Below %d %s" % (speed, unit),
    "أمسك المقود",
    "%d %s يمكن التحكم في التوجيه بسرعات أعلى" % (speed, unit),
    AlertStatus.userPrompt, AlertSize.mid,
    Priority.MID, VisualAlert.steerRequired, AudibleAlert.none, 0., 0.4, .3)


def calibration_incomplete_alert(CP: car.CarParams, sm: messaging.SubMaster, metric: bool) -> Alert:
  speed = int(MIN_SPEED_FILTER * (CV.MS_TO_KPH if metric else CV.MS_TO_MPH))
  unit = "كلم/س" if metric else "ميل"
  return Alert(
    #"Calibration in Progress: %d%%" % sm['liveCalibration'].calPerc,
    #"Drive Above %d %s" % (speed, unit),
    "المعايرة قيد التقدم : %d%%" % sm['liveCalibration'].calPerc,
    "اسرع %d %s بالسيارة" % (speed, unit),
    AlertStatus.normal, AlertSize.mid,
    Priority.LOWEST, VisualAlert.none, AudibleAlert.none, 0., 0., .2)


def no_gps_alert(CP: car.CarParams, sm: messaging.SubMaster, metric: bool) -> Alert:
  gps_integrated = sm['pandaState'].pandaType in [log.PandaState.PandaType.uno, log.PandaState.PandaType.dos]
  return Alert(
    #"Poor GPS reception",
    #"If sky is visible, contact support" if gps_integrated else "Check GPS antenna placement",
    "استقبال ضعيف لنظام تحديد المواقع العالمي (GPS)",
    "تحقق من اتصال GPS والهوائي" if gps_integrated else "تحقق من هوائي GPS",
    AlertStatus.normal, AlertSize.mid,
    Priority.LOWER, VisualAlert.none, AudibleAlert.none, 0., 0., .2, creation_delay=300.)


def wrong_car_mode_alert(CP: car.CarParams, sm: messaging.SubMaster, metric: bool) -> Alert:
  #text = "Cruise Mode Disabled"
  text = "تم تعطيل مثبت السرعة"
  if CP.carName == "honda":
    #text = "Main Switch Off"
    text = "مفتاح إيقاف التشغيل الرئيسي"
  return NoEntryAlert(text, duration_hud_alert=0.)


def startup_fuzzy_fingerprint_alert(CP: car.CarParams, sm: messaging.SubMaster, metric: bool) -> Alert:
  return Alert(
    #"WARNING: No Exact Match on Car Model",
    #f"Closest Match: {CP.carFingerprint.title()[:40]}",
    "تحذير: لم يتم العثور على طراز السيارة المطابق تمامًا",
    f"أقرب نتيجة: {CP.carFingerprint.title()[:40]}",
    AlertStatus.userPrompt, AlertSize.mid,
    Priority.LOWER, VisualAlert.none, AudibleAlert.none, 0., 0., 10.)


def joystick_alert(CP: car.CarParams, sm: messaging.SubMaster, metric: bool) -> Alert:
  axes = sm['testJoystick'].axes
  gb, steer = list(axes)[:2] if len(axes) else (0., 0.)
  return Alert(
    #"Joystick Mode",
    "وضع التحكم بيد الألعاب",
    f"Gas: {round(gb * 100.)}%, Steer: {round(steer * 100.)}%",
    AlertStatus.normal, AlertSize.mid,
    Priority.LOW, VisualAlert.none, AudibleAlert.none, 0., 0., .1)

def auto_lane_change_alert(CP, sm, metric):
  alc_timer = sm['lateralPlan'].autoLaneChangeTimer
  return Alert(
    "تغيير السيارة %dيبدأ في ثوان" % alc_timer,
    "افحص السيارة في المسار",
    AlertStatus.normal, AlertSize.mid,
    Priority.LOW, VisualAlert.none, AudibleAlert.chimeDingRepeat, .1, .1, .1, alert_rate=0.75)

EVENTS: Dict[int, Dict[str, Union[Alert, Callable[[Any, messaging.SubMaster, bool], Alert]]]] = {
  # ********** events with no alerts **********

  EventName.stockFcw: {},

  # ********** events only containing alerts displayed in all states **********

  EventName.joystickDebug: {
    ET.WARNING: joystick_alert,
    ET.PERMANENT: Alert(
      #"Joystick Mode",
      "وضع التحكم بيد الألعاب",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOWER, VisualAlert.none, AudibleAlert.none, 0., 0., 0.1),
  },

  EventName.controlsInitializing: {
    #ET.NO_ENTRY: NoEntryAlert("Controls Initializing"),
    ET.NO_ENTRY: NoEntryAlert("العملية قيد التهيئة"),
  },

  EventName.startup: {
    ET.PERMANENT: Alert(
      #"Be ready to take over at any time",
      #"Always keep hands on wheel and eyes on road",
      "كن مستعدًا لتولي القيادة في أي وقت",
      "امسك عجلة القيادة دائمًا وراقب الطريق",
      AlertStatus.normal, AlertSize.mid,
      Priority.LOWER, VisualAlert.none, AudibleAlert.chimeReady, 1., 0., 10.),
  },

  EventName.startupMaster: {
    ET.PERMANENT: Alert(
      #"WARNING: This branch is not tested",
      #"Always keep hands on wheel and eyes on road",
      "تحذير: لم يتم اختبار هذا الفرع",
      "امسك عجلة القيادة دائمًا وراقب الطريق",
      AlertStatus.normal, AlertSize.mid,
      Priority.LOWER, VisualAlert.none, AudibleAlert.chimeReady, 1., 0., 10.),
  },

  # Car is recognized, but marked as dashcam only
  EventName.startupNoControl: {
    ET.PERMANENT: Alert(
      #"Dashcam mode",
      #"Always keep hands on wheel and eyes on road",
      "وضع كاميرا المراقبة",
      "امسك عجلة القيادة دائمًا وراقب الطريق",
      AlertStatus.normal, AlertSize.mid,
      Priority.LOWER, VisualAlert.none, AudibleAlert.none, 1., 0., 10.),
  },

  # Car is not recognized
  EventName.startupNoCar: {
    ET.PERMANENT: Alert(
      #"Dashcam mode for unsupported car",
      #"Always keep hands on wheel and eyes on road",
      "وضع كاميرا المراقبة : المركبة غير متوافقة",
      "امسك عجلة القيادة دائمًا وراقب الطريق",
      AlertStatus.normal, AlertSize.mid,
      Priority.LOWER, VisualAlert.none, AudibleAlert.none, 1., 0., 10.),
  },

  # openpilot uses the version strings from various ECUs to detect the correct car model.
  # Usually all ECUs are recognized and an exact match to a car model can be made. Sometimes
  # one or two ECUs have unrecognized versions, but the others are present in the database.
  # If openpilot is confident about the match to a car model, it fingerprints anyway.
  # In this case an alert is thrown since there is a small chance the wrong car was detected
  # and the user should pay extra attention.
  # This alert can be prevented by adding all ECU firmware version to openpilot:
  # https://github.com/commaai/openpilot/wiki/Fingerprinting
  EventName.startupFuzzyFingerprint: {
    ET.PERMANENT: startup_fuzzy_fingerprint_alert,
  },

  EventName.startupNoFw: {
    ET.PERMANENT: Alert(
      #"Car Unrecognized",
      #"Check All Connections",
      "لم يتم التعرف على السيارة",
      "تحقق من حالة الاتصال",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.LOWER, VisualAlert.none, AudibleAlert.none, 0., 0., 10.),
  },

  EventName.dashcamMode: {
    ET.PERMANENT: Alert(
      #"Dashcam Mode",
      "وضع كاميرا المراقبة",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOWEST, VisualAlert.none, AudibleAlert.none, 0., 0., .2),
  },

  EventName.invalidLkasSetting: {
    ET.PERMANENT: Alert(
      #"Stock LKAS is turned on",
      #"Turn off stock LKAS to engage",
      "تم تشغيل Stock LKAS",
      "يتم تنشيطه بعد إيقاف تشغيل زر LKAS في السيارة",
      AlertStatus.normal, AlertSize.mid,
      Priority.LOWER, VisualAlert.none, AudibleAlert.none, 0., 0., .2),
  },

  # Some features or cars are marked as community features. If openpilot
  # detects the use of a community feature it switches to dashcam mode
  # until these features are allowed using a toggle in settings.
  EventName.communityFeatureDisallowed: {
    # LOW priority to overcome Cruise Error
    ET.PERMANENT: Alert(
      #"openpilot Not Available",
      #"Enable Community Features in Settings to Engage",
      "أوبن بايلوت غير متوفر",
      "قم بتمكين ميزات المجتمع في الإعدادات للمشاركة",
      AlertStatus.normal, AlertSize.mid,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, 0., 0., .2),
  },

  # openpilot doesn't recognize the car. This switches openpilot into a
  # read-only mode. This can be solved by adding your fingerprint.
  # See https://github.com/commaai/openpilot/wiki/Fingerprinting for more information
  EventName.carUnrecognized: {
    ET.PERMANENT: Alert(
      #"Dashcam Mode",
      #"Car Unrecognized",
      "وضع كاميرا المراقبة",
      "لم يتم التعرف على المركبة",
      AlertStatus.normal, AlertSize.mid,
      Priority.LOWEST, VisualAlert.none, AudibleAlert.none, 0., 0., .2),
  },

  EventName.stockAeb: {
    ET.PERMANENT: Alert(
      #"BRAKE!",
      #"Stock AEB: Risk of Collision",
      "الفرامل!",
      "فرملة الطوارئ : خطر الاصطدام",
      AlertStatus.critical, AlertSize.full,
      Priority.HIGHEST, VisualAlert.fcw, AudibleAlert.none, 1., 2., 2.),
    #ET.NO_ENTRY: NoEntryAlert("Stock AEB: Risk of Collision"),
    ET.NO_ENTRY: NoEntryAlert("AEB: خطر الاصطدام"),
  },

  EventName.fcw: {
    ET.PERMANENT: Alert(
      #"BRAKE!",
      #"Risk of Collision",
      "الفرامل!",
      "فرملة الطوارئ : خطر الاصطدام",
      AlertStatus.critical, AlertSize.full,
      Priority.HIGHEST, VisualAlert.fcw, AudibleAlert.chimeWarningRepeat, 1., 2., 2.),
  },

  EventName.ldw: {
    ET.PERMANENT: Alert(
      #"TAKE CONTROL",
      #"Lane Departure Detected",
      "قم بالتحكم على الفور",
      "تم الكشف عن مغادرة الحارة المرورية",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.LOW, VisualAlert.ldw, AudibleAlert.chimeDing, .1, 2., 3.),
  },

  # ********** events only containing alerts that display while engaged **********

  EventName.gasPressed: {
    ET.PRE_ENABLE: Alert(
      #"openpilot will not brake while gas pressed",
      "لن يقوم برنامج أوبن بايلوت  بالفرملة أثناء الضغط على دواسة الوقود",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOWEST, VisualAlert.none, AudibleAlert.none, .0, .0, .1, creation_delay=1.),
  },

  # openpilot tries to learn certain parameters about your car by observing
  # how the car behaves to steering inputs from both human and openpilot driving.
  # This includes:
  # - steer ratio: gear ratio of the steering rack. Steering angle divided by tire angle
  # - tire stiffness: how much grip your tires have
  # - angle offset: most steering angle sensors are offset and measure a non zero angle when driving straight
  # This alert is thrown when any of these values exceed a sanity check. This can be caused by
  # bad alignment or bad sensor data. If this happens consistently consider creating an issue on GitHub
  EventName.vehicleModelInvalid: {
    #ET.NO_ENTRY: NoEntryAlert("Vehicle Parameter Identification Failed"),
    #ET.SOFT_DISABLE: SoftDisableAlert("Vehicle Parameter Identification Failed"),
    ET.NO_ENTRY: NoEntryAlert("خطأ في تحديد نوع السيارة"),
    ET.SOFT_DISABLE: SoftDisableAlert("خطأ في تحديد نوع السيارة"),
    ET.WARNING: Alert(
      #"Vehicle Parameter Identification Failed",
      "خطأ في تحديد نوع السيارة",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOWEST, VisualAlert.steerRequired, AudibleAlert.none, .0, .0, .1),
  },

  EventName.steerTempUnavailableSilent: {
    ET.WARNING: Alert(
      #"Steering Temporarily Unavailable",
      "التحكم في التوجيه غير متاح مؤقتًا",
      "",
      AlertStatus.userPrompt, AlertSize.small,
      Priority.LOW, VisualAlert.steerRequired, AudibleAlert.chimePrompt, 1., 1., 1.),
  },

  EventName.preDriverDistracted: {
    ET.WARNING: Alert(
      #"KEEP EYES ON ROAD: Driver Distracted",
      "إبقاء العينين على الطريق: السائق مشتت",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOW, VisualAlert.none, AudibleAlert.chimeDing, .1, .1, .1),
  },

  EventName.promptDriverDistracted: {
    ET.WARNING: Alert(
      #"KEEP EYES ON ROAD",
      #"Driver Distracted",
      "ابق عينيك على الطريق",
      "السائق مشتت",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.MID, VisualAlert.steerRequired, AudibleAlert.chimeDing, .1, .1, .1),
  },

  EventName.driverDistracted: {
    ET.WARNING: Alert(
      #"DISENGAGE IMMEDIATELY",
      #"Driver Distracted",
      "افصل على الفور",
      "السائق مشتت",
      AlertStatus.critical, AlertSize.full,
      Priority.HIGH, VisualAlert.steerRequired, AudibleAlert.chimeWarningRepeat, .1, .1, .1),
  },

  EventName.preDriverUnresponsive: {
    ET.WARNING: Alert(
      #"TOUCH STEERING WHEEL: No Face Detected",
      "المس عجلة القيادة : لم يتم اكتشاف أي وجه",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOW, VisualAlert.steerRequired, AudibleAlert.chimeDing, .1, .1, .1, alert_rate=0.75),
  },

  EventName.promptDriverUnresponsive: {
    ET.WARNING: Alert(
      #"TOUCH STEERING WHEEL",
      #"Driver Unresponsive",
      "المس عجلة القيادة",
      "السائق لا يستجيب",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.MID, VisualAlert.steerRequired, AudibleAlert.chimeWarning2Repeat, .1, .1, .1),
  },

  EventName.driverUnresponsive: {
    ET.WARNING: Alert(
      #"DISENGAGE IMMEDIATELY",
      #"Driver Unresponsive",
      "افصل على الفور",
      "السائق لا يستجيب",
      AlertStatus.critical, AlertSize.full,
      Priority.HIGH, VisualAlert.steerRequired, AudibleAlert.chimeWarningRepeat, .1, .1, .1),
  },

  EventName.manualRestart: {
    ET.WARNING: Alert(
      #"TAKE CONTROL",
      #"Resume Driving Manually",
      "امسك عجلة القيادة",
      "استئناف القيادة يدويًا",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, 0., 0., .2),
  },

  EventName.resumeRequired: {
    ET.WARNING: Alert(
      #"STOPPED",
      #"Press Resume to Move",
      "توقفت",
      "اضغط على استئناف للتحرك",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, 0., 0., .2),
  },

  EventName.belowSteerSpeed: {
    ET.WARNING: below_steer_speed_alert,
  },

  EventName.preLaneChangeLeft: {
    ET.WARNING: Alert(
      #"Steer Left to Start Lane Change Once Safe",
      #"",
      "توجه يسارًا لبدء تغيير المسار بمجرد أن يصبح آمنًا",
      "",
      AlertStatus.normal, AlertSize.mid,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, .0, .1, .1, alert_rate=0.75),
  },

  EventName.preLaneChangeRight: {
    ET.WARNING: Alert(
      #"Steer Right to Start Lane Change Once Safe",
      #"",
      "اتجه يمينًا لبدء تغيير المسار بمجرد أن يصبح آمنًا",
      "",
      AlertStatus.normal, AlertSize.mid,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, .0, .1, .1, alert_rate=0.75),
  },

  EventName.laneChangeBlocked: {
    ET.WARNING: Alert(
      #"Car Detected in Blindspot",
      #"",
      "تم اكتشاف السيارة في النقطة العمياء",
      "",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.LOW, VisualAlert.none, AudibleAlert.chimeDingRepeat, .1, .1, .1),
  },

  EventName.laneChange: {
    ET.WARNING: Alert(
      #"Changing Lanes",
      #"",
      "تغيير المسارات",
      "",
      AlertStatus.normal, AlertSize.mid,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, .0, .1, .1),
  },

  EventName.steerSaturated: {
    ET.WARNING: Alert(
      #"TAKE CONTROL",
      #"Turn Exceeds Steering Limit",
      "قم بالتحكم",
      "يتخطى المنعطف حد التوجيه",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.LOW, VisualAlert.steerRequired, AudibleAlert.chimePrompt, 1., 1., 1.),
  },

  # Thrown when the fan is driven at >50% but is not rotating
  EventName.fanMalfunction: {
    #ET.PERMANENT: NormalPermanentAlert("Fan Malfunction", "Contact Support"),
    ET.PERMANENT: NormalPermanentAlert("عطل في المروحة", "تحقق من جهازك"),
  },

  # Camera is not outputting frames at a constant framerate
  EventName.cameraMalfunction: {
    #ET.PERMANENT: NormalPermanentAlert("Camera Malfunction", "Contact Support"),
    ET.PERMANENT: NormalPermanentAlert("عطل في الكاميرا", "اتصل بالدعم"),
  },

  # Unused
  EventName.gpsMalfunction: {
    #ET.PERMANENT: NormalPermanentAlert("GPS Malfunction", "Contact Support"),
    ET.PERMANENT: NormalPermanentAlert("عطل في نظام تحديد المواقع العالمي (GPS)", "اتصل بالدعم"),
  },

  # When the GPS position and localizer diverge the localizer is reset to the
  # current GPS position. This alert is thrown when the localizer is reset
  # more often than expected.
  EventName.localizerMalfunction: {
    #ET.PERMANENT: NormalPermanentAlert("Sensor Malfunction", "Contact Support"),
    ET.PERMANENT: NormalPermanentAlert("عطل في جهاز الاستشعار", "اتصل بالدعم"),
  },

  EventName.turningIndicatorOn: {
    ET.WARNING: Alert(
      "يرجى الضغط على عجلة القيادة أثناء تشغيل ضوء إشارة الانعطاف",
      "",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.MID, VisualAlert.none, AudibleAlert.none, .0, .1, .2),
  },

  EventName.lkasButtonOff: {
    ET.WARNING: Alert(
      "يرجى التحقق من زر LKAS على السيارة",
      "",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.HIGH, VisualAlert.steerRequired, AudibleAlert.none, 0., .1, .2),
  },

  EventName.autoLaneChange: {
    ET.WARNING: auto_lane_change_alert,
  },

  # ********** events that affect controls state transitions **********

  EventName.pcmEnable: {
    ET.ENABLE: EngagementAlert(AudibleAlert.chimeEngage),
  },

  EventName.buttonEnable: {
    ET.ENABLE: EngagementAlert(AudibleAlert.chimeEngage),
  },

  EventName.pcmDisable: {
    ET.USER_DISABLE: EngagementAlert(AudibleAlert.chimeDisengage),
  },

  EventName.buttonCancel: {
    ET.USER_DISABLE: EngagementAlert(AudibleAlert.chimeDisengage),
  },

  EventName.brakeHold: {
    ET.USER_DISABLE: EngagementAlert(AudibleAlert.chimeDisengage),
    #ET.NO_ENTRY: NoEntryAlert("Brake Hold Active"),
    ET.NO_ENTRY: NoEntryAlert("تثبيت الفرامل نشط"),
  },

  EventName.parkBrake: {
    ET.USER_DISABLE: EngagementAlert(AudibleAlert.chimeDisengage),
    #ET.NO_ENTRY: NoEntryAlert("Park Brake Engaged"),
    ET.NO_ENTRY: NoEntryAlert("تفعيل الجلنط الكخربائي"),
  },

  EventName.pedalPressed: {
    ET.USER_DISABLE: EngagementAlert(AudibleAlert.chimeDisengage),
    #ET.NO_ENTRY: NoEntryAlert("Pedal Pressed During Attempt",
    ET.NO_ENTRY: NoEntryAlert("الكشف عن الفرامل",
                              visual_alert=VisualAlert.brakePressed),
  },

  EventName.wrongCarMode: {
    ET.USER_DISABLE: EngagementAlert(AudibleAlert.chimeDisengage),
    ET.NO_ENTRY: wrong_car_mode_alert,
  },

  EventName.wrongCruiseMode: {
    ET.USER_DISABLE: EngagementAlert(AudibleAlert.chimeDisengage),
    #ET.NO_ENTRY: NoEntryAlert("Enable Adaptive Cruise"),
    ET.NO_ENTRY: NoEntryAlert("تفعيل مثبت السرعة الذكي"),
  },

  EventName.steerTempUnavailable: {
    #ET.SOFT_DISABLE: SoftDisableAlert("Steering Temporarily Unavailable"),
    #ET.NO_ENTRY: NoEntryAlert("Steering Temporarily Unavailable",
    ET.WARNING: Alert(
      "امسك عجلة القيادة",
      "التحكم في التوجيه غير متاح مؤقتًا",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.LOW, VisualAlert.steerRequired, AudibleAlert.none, 0., 0., .2),
    ET.NO_ENTRY: NoEntryAlert("التحكم في التوجيه غير متاح مؤقتًا",
                              duration_hud_alert=0.),
  },

  EventName.outOfSpace: {
    ET.PERMANENT: Alert(
      #"Out of Storage",
      "الذاكرة ممتلئة",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOWER, VisualAlert.none, AudibleAlert.none, 0., 0., .2),
    #ET.NO_ENTRY: NoEntryAlert("Out of Storage Space",
    ET.NO_ENTRY: NoEntryAlert("نفاد مساحة التخزين",
                              duration_hud_alert=0.),
  },

  EventName.belowEngageSpeed: {
    #ET.NO_ENTRY: NoEntryAlert("Speed Too Low"),
    ET.NO_ENTRY: NoEntryAlert("السرعة منخفضة للغاية"),
  },

  EventName.sensorDataInvalid: {
    ET.PERMANENT: Alert(
      #"No Data from Device Sensors",
      #"Reboot your Device",
      "لا توجد بيانات من أجهزة استشعار الجهاز",
      "أعد تشغيل الجهاز",
      AlertStatus.normal, AlertSize.mid,
      Priority.LOWER, VisualAlert.none, AudibleAlert.none, 0., 0., .2, creation_delay=1.),
    #ET.NO_ENTRY: NoEntryAlert("No Data from Device Sensors"),
    ET.NO_ENTRY: NoEntryAlert("لا توجد بيانات من أجهزة استشعار الجهاز"),
  },

  EventName.noGps: {
    ET.PERMANENT: no_gps_alert,
  },

  EventName.soundsUnavailable: {
    #ET.PERMANENT: NormalPermanentAlert("Speaker not found", "Reboot your Device"),
    #ET.NO_ENTRY: NoEntryAlert("Speaker not found"),
    ET.PERMANENT: NormalPermanentAlert("مكبر الصوت غير موجود", "أعد تشغيل الجهاز"),
    ET.NO_ENTRY: NoEntryAlert("مكبر الصوت غير موجود"),
  },

  EventName.tooDistracted: {
    #ET.NO_ENTRY: NoEntryAlert("Distraction Level Too High"),
    ET.NO_ENTRY: NoEntryAlert("مستوى الإلهاء مرتفع جدًا"),
  },

  EventName.overheat: {
    ET.PERMANENT: Alert(
      #"System Overheated",
      "النظام ساخن",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOWER, VisualAlert.none, AudibleAlert.none, 0., 0., .2),
    #ET.SOFT_DISABLE: SoftDisableAlert("System Overheated"),
    #ET.NO_ENTRY: NoEntryAlert("System Overheated"),
    ET.SOFT_DISABLE: SoftDisableAlert("النظام ساخن"),
    ET.NO_ENTRY: NoEntryAlert("النظام ساخن"),
  },

  EventName.wrongGear: {
    #ET.SOFT_DISABLE: SoftDisableAlert("Gear not D"),
    #ET.NO_ENTRY: NoEntryAlert("Gear not D"),
    ET.USER_DISABLE: EngagementAlert(AudibleAlert.chimeDisengage),
    ET.NO_ENTRY: NoEntryAlert("تغيير الترس إلى [D]",
                              audible_alert=AudibleAlert.chimeGeard, duration_sound=3.),
  },

  # This alert is thrown when the calibration angles are outside of the acceptable range.
  # For example if the device is pointed too much to the left or the right.
  # Usually this can only be solved by removing the mount from the windshield completely,
  # and attaching while making sure the device is pointed straight forward and is level.
  # See https://comma.ai/setup for more information
  EventName.calibrationInvalid: {
    #ET.PERMANENT: NormalPermanentAlert("Calibration Invalid", "Remount Device and Recalibrate"),
    #ET.SOFT_DISABLE: SoftDisableAlert("Calibration Invalid: Remount Device & Recalibrate"),
    #ET.NO_ENTRY: NoEntryAlert("Calibration Invalid: Remount Device & Recalibrate"),
    ET.PERMANENT: NormalPermanentAlert("خطأ في المعايرة "," أعد المعايرة بعد تغيير موقع الجهاز."),
    ET.SOFT_DISABLE: SoftDisableAlert("خطأ في المعايرة: أعد المعايرة بعد تغيير موقع الجهاز"),
    ET.NO_ENTRY: NoEntryAlert("خطأ في المعايرة: أعد المعايرة بعد تغيير موقع الجهاز"),
  },

  EventName.calibrationIncomplete: {
    ET.PERMANENT: calibration_incomplete_alert,
    #ET.SOFT_DISABLE: SoftDisableAlert("Calibration in Progress"),
    #ET.NO_ENTRY: NoEntryAlert("Calibration in Progress"),
    ET.SOFT_DISABLE: SoftDisableAlert("المعايرة قيد التقدم"),
    ET.NO_ENTRY: NoEntryAlert("المعايرة قيد التقدم"),
  },

  EventName.doorOpen: {
    #ET.SOFT_DISABLE: SoftDisableAlert("Door Open"),
    #ET.NO_ENTRY: NoEntryAlert("Door Open"),
    ET.PERMANENT: Alert(
      "الباب مفتوح",
      "",
      AlertStatus.normal, AlertSize.full,
      Priority.LOWEST, VisualAlert.none, AudibleAlert.none, 0., 0., .2, creation_delay=0.5),
    ET.USER_DISABLE: EngagementAlert(AudibleAlert.chimeDisengage),
    ET.NO_ENTRY: NoEntryAlert("الباب مفتوح"),
  },

  EventName.seatbeltNotLatched: {
    #ET.SOFT_DISABLE: SoftDisableAlert("Seatbelt Unlatched"),
    #ET.NO_ENTRY: NoEntryAlert("Seatbelt Unlatched"),
    ET.PERMANENT: Alert(
      "الرجاء ربط حزام الأمان",
      "",
      AlertStatus.normal, AlertSize.full,
      Priority.LOWEST, VisualAlert.none, AudibleAlert.none, 0., 0., .2, creation_delay=0.5),
    ET.SOFT_DISABLE: SoftDisableAlert("الرجاء ربط حزام الأمان الخاص بك"),
    ET.NO_ENTRY: NoEntryAlert("الرجاء ربط حزام الأمان الخاص بك",
                              audible_alert=AudibleAlert.chimeSeatbelt, duration_sound=3.),
  },

  EventName.espDisabled: {
    #ET.SOFT_DISABLE: SoftDisableAlert("ESP Off"),
    #ET.NO_ENTRY: NoEntryAlert("ESP Off"),
    ET.SOFT_DISABLE: SoftDisableAlert("إيقاف ESP"),
    ET.NO_ENTRY: NoEntryAlert("إيقاف ESP"),
  },

  EventName.lowBattery: {
    #ET.SOFT_DISABLE: SoftDisableAlert("Low Battery"),
    #ET.NO_ENTRY: NoEntryAlert("Low Battery"),
    ET.SOFT_DISABLE: SoftDisableAlert("البطارية ضعيفة"),
    ET.NO_ENTRY: NoEntryAlert("البطارية ضعيفة"),
  },

  # Different openpilot services communicate between each other at a certain
  # interval. If communication does not follow the regular schedule this alert
  # is thrown. This can mean a service crashed, did not broadcast a message for
  # ten times the regular interval, or the average interval is more than 10% too high.
  EventName.commIssue: {
    #ET.SOFT_DISABLE: SoftDisableAlert("Communication Issue between Processes"),
    #ET.NO_ENTRY: NoEntryAlert("Communication Issue between Processes",
    ET.SOFT_DISABLE: SoftDisableAlert("خطأ في عملية الجهاز"),
    ET.NO_ENTRY: NoEntryAlert("خطأ في عملية الجهاز",
                              audible_alert=AudibleAlert.chimeDisengage),
  },

  # Thrown when manager detects a service exited unexpectedly while driving
  EventName.processNotRunning: {
    #ET.NO_ENTRY: NoEntryAlert("System Malfunction: Reboot Your Device",
    ET.NO_ENTRY: NoEntryAlert("عطل في النظام: أعد تشغيل الجهاز",
                              audible_alert=AudibleAlert.chimeDisengage),
  },

  EventName.radarFault: {
    #ET.SOFT_DISABLE: SoftDisableAlert("Radar Error: Restart the Car"),
    #ET.NO_ENTRY: NoEntryAlert("Radar Error: Restart the Car"),
    ET.SOFT_DISABLE: SoftDisableAlert("خطأ الرادار: أعد تشغيل السيارة"),
    ET.NO_ENTRY: NoEntryAlert("خطأ الرادار: أعد تشغيل السيارة"),
  },

  # Every frame from the camera should be processed by the model. If modeld
  # is not processing frames fast enough they have to be dropped. This alert is
  # thrown when over 20% of frames are dropped.
  EventName.modeldLagging: {
    #ET.SOFT_DISABLE: SoftDisableAlert("Driving model lagging"),
    #ET.NO_ENTRY: NoEntryAlert("Driving model lagging"),
    ET.SOFT_DISABLE: SoftDisableAlert("نموذج القيادة تأخر"),
    ET.NO_ENTRY: NoEntryAlert("نموذج القيادة تأخر"),
  },

  # Besides predicting the path, lane lines and lead car data the model also
  # predicts the current velocity and rotation speed of the car. If the model is
  # very uncertain about the current velocity while the car is moving, this
  # usually means the model has trouble understanding the scene. This is used
  # as a heuristic to warn the driver.
  EventName.posenetInvalid: {
    #ET.SOFT_DISABLE: SoftDisableAlert("Model Output Uncertain"),
    #ET.NO_ENTRY: NoEntryAlert("Model Output Uncertain"),
    ET.SOFT_DISABLE: SoftDisableAlert("يرجى القيادة بحذر لأن حالة التعرف على الحارة ليست جيدة."),
    ET.NO_ENTRY: NoEntryAlert("يرجى القيادة بحذر لأن حالة التعرف على الحارة ليست جيدة."),
  },

  # When the localizer detects an acceleration of more than 40 m/s^2 (~4G) we
  # alert the driver the device might have fallen from the windshield.
  EventName.deviceFalling: {
    #ET.SOFT_DISABLE: SoftDisableAlert("Device Fell Off Mount"),
    #ET.NO_ENTRY: NoEntryAlert("Device Fell Off Mount"),
    ET.SOFT_DISABLE: SoftDisableAlert("الجهاز وقع عن القاعدة"),
    ET.NO_ENTRY: NoEntryAlert("الجهاز وقع عن القاعدة"),
  },

  EventName.lowMemory: {
    #ET.SOFT_DISABLE: SoftDisableAlert("Low Memory: Reboot Your Device"),
    #ET.PERMANENT: NormalPermanentAlert("Low Memory", "Reboot your Device"),
    #ET.NO_ENTRY: NoEntryAlert("Low Memory: Reboot Your Device",
    ET.SOFT_DISABLE: SoftDisableAlert("ذاكرة غير كافية: أعد تشغيل الجهاز"),
    ET.PERMANENT: NormalPermanentAlert("ذاكرة غير كافية "," الرجاء إعادة تشغيل جهازك "),
    ET.NO_ENTRY: NoEntryAlert("ذاكرة غير كافية: أعد تشغيل الجهاز",
                              audible_alert=AudibleAlert.chimeDisengage),
  },

  EventName.highCpuUsage: {
    #ET.SOFT_DISABLE: SoftDisableAlert("System Malfunction: Reboot Your Device"),
    #ET.PERMANENT: NormalPermanentAlert("System Malfunction", "Reboot your Device"),
    ET.NO_ENTRY: NoEntryAlert("عطل في النظام: أعد تشغيل جهازك",
                              audible_alert=AudibleAlert.chimeDisengage),
  },

  EventName.accFaulted: {
    #ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("Cruise Faulted"),
    #ET.PERMANENT: NormalPermanentAlert("Cruise Faulted", ""),
    #ET.NO_ENTRY: NoEntryAlert("Cruise Faulted"),
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("خطأ الرحلة"),
    ET.PERMANENT: NormalPermanentAlert("خطأ الرحلة", ""),
    ET.NO_ENTRY: NoEntryAlert("خطأ الرحلة"),
  },

  EventName.controlsMismatch: {
    #ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("Controls Mismatch"),
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("عدم تطابق التحكم"),
  },

  EventName.roadCameraError: {
    #ET.PERMANENT: NormalPermanentAlert("Road Camera Error", "",
    ET.PERMANENT: NormalPermanentAlert("خطأ في كاميرا الطريق", "",
                                       duration_text=10.),
  },

  EventName.driverCameraError: {
    #ET.PERMANENT: NormalPermanentAlert("Driver Camera Error", "",
    ET.PERMANENT: NormalPermanentAlert("خطأ في كاميرا الطريق", "",
                                       duration_text=10.),
  },

  EventName.wideRoadCameraError: {
    #ET.PERMANENT: NormalPermanentAlert("Wide Road Camera Error", "",
    ET.PERMANENT: NormalPermanentAlert("خطأ كاميرا الطريق العريضة", "",
                                       duration_text=10.),
  },

  # Sometimes the USB stack on the device can get into a bad state
  # causing the connection to the panda to be lost
  EventName.usbError: {
    #ET.SOFT_DISABLE: SoftDisableAlert("USB Error: Reboot Your Device"),
    #ET.PERMANENT: NormalPermanentAlert("USB Error: Reboot Your Device", ""),
    #ET.NO_ENTRY: NoEntryAlert("USB Error: Reboot Your Device"),
    ET.SOFT_DISABLE: SoftDisableAlert("خطأ USB: أعد تشغيل جهازك"),
    ET.PERMANENT: NormalPermanentAlert("خطأ USB: أعد تشغيل جهازك", ""),
    ET.NO_ENTRY: NoEntryAlert("خطأ USB: أعد تشغيل جهازك"),
  },

  # This alert can be thrown for the following reasons:
  # - No CAN data received at all
  # - CAN data is received, but some message are not received at the right frequency
  # If you're not writing a new car port, this is usually cause by faulty wiring
  EventName.canError: {
    #ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("CAN Error: Check Connections"),
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert(" خطأ في الكان: تحقق من التوصيلات"),
    ET.PERMANENT: Alert(
      #"CAN Error: Check Connections",
      "خطأ في الكان: تحقق من التوصيلات",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, 0., 0., .2, creation_delay=1.),
    #ET.NO_ENTRY: NoEntryAlert("CAN Error: Check Connections"),
    ET.NO_ENTRY: NoEntryAlert("خطأ في الكان: تحقق من التوصيلات"),
  },

  EventName.steerUnavailable: {
    #ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("LKAS Fault: Restart the Car"),
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("خطأ LKAS: أعد تشغيل السيارة"),
    ET.PERMANENT: Alert(
      #"LKAS Fault: Restart the car to engage",
      "خطأ LKAS: أعد تشغيل السيارة",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOWER, VisualAlert.none, AudibleAlert.none, 0., 0., .2),
    #ET.NO_ENTRY: NoEntryAlert("LKAS Fault: Restart the Car"),
    ET.NO_ENTRY: NoEntryAlert("خطأ LKAS: أعد تشغيل السيارة"),
  },

  EventName.brakeUnavailable: {
    #ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("Cruise Fault: Restart the Car"),
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("خطأ في مثبت السرعة : أعد تشغيل السيارة"),
    ET.PERMANENT: Alert(
      #"Cruise Fault: Restart the car to engage",
      "خطأ في مثبت السرعة : أعد تشغيل السيارة",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOWER, VisualAlert.none, AudibleAlert.none, 0., 0., .2),
    #ET.NO_ENTRY: NoEntryAlert("Cruise Fault: Restart the Car"),
    ET.NO_ENTRY: NoEntryAlert("خطأ في مثبت السرعة : أعد تشغيل السيارة"),
  },

  EventName.reverseGear: {
    ET.PERMANENT: Alert(
      #"Reverse\nGear",
      "حالة القير [R]",
      "",
      AlertStatus.normal, AlertSize.full,
      Priority.LOWEST, VisualAlert.none, AudibleAlert.none, 0., 0., .2, creation_delay=0.5),
    #ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("Reverse Gear"),
    #ET.NO_ENTRY: NoEntryAlert("Reverse Gear"),
    ET.USER_DISABLE: EngagementAlert(AudibleAlert.chimeDisengage),
    ET.NO_ENTRY: NoEntryAlert("حالة القير [R]"),
  },

  # On cars that use stock ACC the car can decide to cancel ACC for various reasons.
  # When this happens we can no long control the car so the user needs to be warned immediately.
  EventName.cruiseDisabled: {
    #ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("Cruise Is Off"),
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("مثبت السرعة مظفئ"),
  },

  # For planning the trajectory Model Predictive Control (MPC) is used. This is
  # an optimization algorithm that is not guaranteed to find a feasible solution.
  # If no solution is found or the solution has a very high cost this alert is thrown.
  EventName.plannerError: {
    #ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("Planner Solution Error"),
    #ET.NO_ENTRY: NoEntryAlert("Planner Solution Error"),
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("خطاء في مسار الرحلة"),
    ET.NO_ENTRY: NoEntryAlert("خطاء في مسار الرحلة"),
  },

  # When the relay in the harness box opens the CAN bus between the LKAS camera
  # and the rest of the car is separated. When messages from the LKAS camera
  # are received on the car side this usually means the relay hasn't opened correctly
  # and this alert is thrown.
  EventName.relayMalfunction: {
    #ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("Harness Malfunction"),
    #ET.PERMANENT: NormalPermanentAlert("Harness Malfunction", "Check Hardware"),
    #ET.NO_ENTRY: NoEntryAlert("Harness Malfunction"),
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("عطل في الظفيرة"),
    ET.PERMANENT: NormalPermanentAlert("عطل في الظفيرة", "تحقق من الأجهزة"),
    ET.NO_ENTRY: NoEntryAlert("عطل في الظفيرة"),
  },

  EventName.noTarget: {
    ET.IMMEDIATE_DISABLE: Alert(
      #"openpilot Canceled",
      #"No close lead car",
      "تم إلغاء الأوبن بايلوت",
      "لا توجد سيارة في المقدمة",
      AlertStatus.normal, AlertSize.mid,
      Priority.HIGH, VisualAlert.none, AudibleAlert.chimeDisengage, .4, 2., 3.),
    #ET.NO_ENTRY: NoEntryAlert("No Close Lead Car"),
    ET.NO_ENTRY: NoEntryAlert("لا توجد سيارة في المقدمة"),
  },

  EventName.speedTooLow: {
    ET.IMMEDIATE_DISABLE: Alert(
      #"openpilot Canceled",
      #"Speed too low",
      "تم إلغاء الأوبن بايلوت",
      "السرعة منخفضة جدا",
      AlertStatus.normal, AlertSize.mid,
      Priority.HIGH, VisualAlert.none, AudibleAlert.chimeDisengage, .4, 2., 3.),
  },

  # When the car is driving faster than most cars in the training data the model outputs can be unpredictable
  EventName.speedTooHigh: {
    ET.WARNING: Alert(
      #"Speed Too High",
      #"Model uncertain at this speed",
      "السرعة عالية جدا",
      "من فضلك أبطء السرعة",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.HIGH, VisualAlert.steerRequired, AudibleAlert.chimeWarning2Repeat, 2.2, 3., 4.),
    ET.NO_ENTRY: Alert(
      #"Speed Too High",
      #"Slow down to engage",
      "السرعة عالية جدا",
      "أخفظ السرعة للتفعيل",
      AlertStatus.normal, AlertSize.mid,
      Priority.LOW, VisualAlert.none, AudibleAlert.chimeError, .4, 2., 3.),
  },

  EventName.lowSpeedLockout: {
    ET.PERMANENT: Alert(
      #"Cruise Fault: Restart the car to engage",
      "خطاء في مثبت السرعة : أعد تشغيل السيارة للتفعيل",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOWER, VisualAlert.none, AudibleAlert.none, 0., 0., .2),
    #ET.NO_ENTRY: NoEntryAlert("Cruise Fault: Restart the Car"),
    ET.NO_ENTRY: NoEntryAlert("خطاء في مثبت السرعة : أعد تشغيل السيارة"),
  },

}
