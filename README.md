
**هذه الملفات مبنية من المهندس أحمد برناوي وفريقه (ناصر الخالدي - ثامر الحميد) لتطوير أنظمة القيادة لهيونداي , كيا , جينسس**

https://github.com/xx979xx/openpilot

إنه مفتوح المصدر ومرخص من معهد ماساتشوستس للتكنولوجيا. بتثبيت هذا البرنامج ، فإنك تتحمل كامل المسؤولية عن أي شيء قد يحدث أثناء استخدامه. جميع المساهمين في هذه الشركة غير مسؤولين. استخدمه على مسؤوليتك الخاصة  <b>استخدام على مسؤوليتك الخاصة.</b>


------------------------------------------------------


![](https://i.imgur.com/JVj5aZc.jpg)

جدول المحتويات
=======================

* [ماهو الأوبن بايلوت؟](#ماهو-الأوبن-بايلوت؟)
* [عمله على السيارة](#running-in-a-car)
* [عمله على الكمبيوتر](#running-on-pc)
* [المجتمع والمساهمة](#community-and-contributing)
* [بينانات المسخدم وحساب كوما](#user-data-and-comma-account)
* [السلامة والاختبار](#safety-and-testing)
* [بنية الدليل](#directory-structure)
* [الترخيص](#licensing)

---

ماهو الأوبن بايلوت ؟
------

[القائد الآلي](http://github.com/commaai/openpilot) هو نظام مفتوح المصدر لمساعدة السائق. حاليًا ، يؤدي برنامج القائد الآلي وظائف التحكم التكيفي في القيادة (ACC) ، وتمركز المسار الآلي (ALC) ، والتحذير من الاصطدام الأمامي (FCW) ، والتحذير من مغادرة المسار (LDW) لمجموعة متزايدة من [السيارات المدعومة والموديلات الحديثة كل عام](docs/CARS.md). بالإضافة أثناء تشغيل الأوبن بايلوت , تعمل كاميرا مراقبة السائق (DM) على مراقبة السائق المشتت الإنتباه والنائم أثناء عمل النظام. لمزيد من المعلومات [ تكامل المركبة ](docs/INTEGRATION.md) و [محدودية](docs/LIMITATIONS.md).

<table>
  <tr>
    <td><a href="https://youtu.be/Asq9IBZ5EL8" title="Video By Greer Viau"><img src="https://i.imgur.com/1aVz6fu.png"></a></td>
    <td><a href="https://youtu.be/YfMKV0BCS3E" title="Video By Logan LeGrand"><img src="https://i.imgur.com/U2kBp1r.jpg"></a></td>
    <td><a href="https://youtu.be/fE3jcvNPKuU" title="Video By Charlie Kim"><img src="https://i.imgur.com/PInrzIG.jpg"></a></td>
    <td><a href="https://youtu.be/CVj5Vxcrl8c" title="Video By Aragon"><img src="https://i.imgur.com/w6cZyoL.jpg"></a></td>
  </tr>
  <tr>
    <td><a href="https://youtu.be/iIUICQkdwFQ" title="Video By Logan LeGrand"><img src="https://i.imgur.com/b1LHQTy.jpg"></a></td>
    <td><a href="https://youtu.be/XOsa0FsVIsg" title="Video By PinoyDrives"><img src="https://i.imgur.com/6FG0Bd8.jpg"></a></td>
    <td><a href="https://youtu.be/bCwcJ98R_Xw" title="Video By JS"><img src="https://i.imgur.com/zO18CbW.jpg"></a></td>
    <td><a href="https://youtu.be/BQ0tF3MTyyc" title="Video By Tsai-Fi"><img src="https://i.imgur.com/eZzelq3.jpg"></a></td>
  </tr>
</table>
 
عمله على السيارة
------

لاستخدام نظام الاوبن بايلوت تحتاج إلى أربعة أشياء
* هذا البرنامج إنه مجاني ومتاح هنا.
* إحدى[ أكثر من 150 سيارة مدعومة ](docs/CARS.md). نحن ندعم هوندا, تويوتا ، هيونداي ، نيسان ، كيا ، كرايسلر ، لكزس ، أكورا ، أودي ، فولكس فاجن ، وأكثر من ذلك. إذا كانت سيارتك غير مدعومة, ولاكن يجب أن يكون لديك نظام مثبت السرعة التكيفي ومساعد الحفاظ على المسار لكي تستطيع تشغيل نظام الاوبن بايلوت على مركبتك
* الجهاز يدهم تشعيل البرنامج [كوما ثلاثة](https://comma.ai/shop/products/two), [كوما ثلاثة](https://comma.ai/shop/products/three), أو إذا كنت ترغب في التجربة, a [كمبيوتر أوبونتو مع كاميرات الويب](https://github.com/commaai/openpilot/tree/master/tools/webcam).
* طريقة للاتصال بسيارتك. باستخدام كوما اثنين أو ثلاثة ، تحتاج فقط إلى ملف [ظفيرة السيارة](https://comma.ai/shop/products/car-harness). مع الايون الذهبي أو الكمبيوتر الشخصي ، تحتاج أيضًا إلى ملف [البلاك باندا](https://comma.ai/shop/products/panda).

لدينا تعليمات مفصلة عن [كيفية تركيب الجهاز في السيارة](https://comma.ai/setup).

عمله على الكمبيوتر
------

يمكن تشغيل جميع خدمات القائد الآلي كالمعتاد على جهاز كمبيوتر ، حتى بدون أجهزة خاصة أو سيارة. لتطوير أو تجربة القائد الآلي ، يمكنك تشغيل القائد الآلي على بيانات مسجلة أو محاكاة.

باستخدام أدوات القائد الآلي ، يمكنك رسم السجلات وإعادة تشغيل محركات الأقراص ومشاهدة تدفقات الكاميرا كاملة الدقة. يرى [the tools README](tools/README.md) للمزيد من المعلومات.

يمكنك أيضًا تشغيل القائد الآلي في المحاكاة [مع محاكي كلارا](tools/sim/README.md). هذا يسمح لبرنامج القائد الآلي بالقيادة حول سيارة افتراضية على جهاز نظام يوبينتو الخاص بك. يجب أن يستغرق الإعداد بالكامل بضع دقائق فقط ، ولكنه يتطلب وحدة معالجة رسومات جيدة.

بعض المزايا المضافة
------
-  شعار التحميل باللغة العربية / فيديو تقديمي أثناء الإقلاع
- عرض الرسائل, واجهة المستخدم باللغة العربية
- عرض التفاف عجلة القيادة , عرض ضغط الإطارات
- الفرامل, النفاط العمياء, الأوتوهولد, عرض نظام تحديد المواقع
- عرض عنوان الآي بي / عرض نسبة شحن البطاريات
- التحكم بعزم الدودة ( PID / INDI / LQR )
- دعم الكاميرا متعددة الوظائف ( LKAS / LDWS / LFA )
- التحكم الطويل ( MAD / LONG )
- شعار NMK / مزايا متعددة / واجهة مستخدم بسيطة

## مراجع لبعض الأكواد المضافة
- https://github.com/commaai/openpilot
- https://github.com/xx979xx/openpilo
- https://github.com/xps-genesis/openpilot
- https://github.com/kegman/openpilot
- https://github.com/dragonpilot-community/dragonpilot
- https://github.com/wirelessnet2/openpilot
- https://github.com/sshane/openpilot
- https://github.com/arne182/ArnePilot
- https://github.com/neokii
- https://github.com/openpilotusers
- https://github.com/Circuit-Pro/openpilot
- - -
## مخططات للعديد من ظفائر المركبات ( هيونداي -كيا - جينسس )

cable order -> https://smartstore.naver.com/hyotrade/products/5341431170

[![](https://i.imgur.com/sRcmaeS.png)](#)
[![](https://i.imgur.com/arZrs6d.png)](#)
[![](https://i.imgur.com/uqJlVrC.jpg)](#)

## فرع شيفرولية بولت
- https://github.com/JasonJShuler/openpilot
- https://github.com/hanabi95/openpilot
- https://github.com/jc01rho-openpilot-BoltEV2019-KoKr
- https://github.com/parksunkyu81
- - -


المجتمع والمساهمة
------

تم تطوير برنامج القائد الآلي بواسطة [كوما](https://comma.ai/) ومن قبل مستخدمين مثلك. نرحب بكل من طلبات الحل والإصلاح [جت هب](http://github.com/commaai/openpilot). يتم تشجيع إصلاحات الأخطاء ومنافذ السيارات الجديدة. التحديث [المستندات المساهمة](docs/CONTRIBUTING.md).

يمكن العثور على الوثائق المتعلقة بتطوير القائد الآلي على [docs.comma.ai](https://docs.comma.ai). معلومات حول تشغيل برنامج القائد الآلي (e.g. FAQ, fingerprinting, troubleshooting, custom forks, community hardware) يجل أن تكون على [ويكي](https://github.com/commaai/openpilot/wiki).

يمكنك إضافة دعم لسيارتك باتباع الإرشادات التي كتبنا عنها [ماركة](https://blog.comma.ai/how-to-write-a-car-port-for-openpilot/) and [الموديل](https://blog.comma.ai/openpilot-port-guide-for-toyota-models/) المنافذ. بشكل عام ، تعتبر السيارة المزودة بنظام تثبيت السرعة التكيفي ونظام المساعدة في الحفاظ على المسار مرشحًا جيدًا. [انضم إلى الديسكورد](https://discord.comma.ai) لمناقشة منافذ السيارات: معظم ماركات السيارات لديها قناة مخصصة.

تريد الحصول على أجر للعمل على القائد الآلي [كوما تقوم بالتوظيف](https://comma.ai/jobs/).

و [تابعنا على تويتر](https://twitter.com/comma_ai).

بينانات المسخدم وحساب كوما
------

بشكل افتراضي ، يقوم برنامج القائد الآلي بتحميل بيانات القيادة إلى خوادمنا. يمكنك أيضًا الوصول إلى بياناتك من خلال [اتصال كوما](https://connect.comma.ai/). نستخدم بياناتك لتدريب نماذج أفضل وتحسين القائد الآلي للجميع.

القائد اللآلي هو برنامج مفتوح المصدر: للمستخدم حرية تعطيل جمع البيانات إذا كان يرغب في ذلك.

يسجل برنامج القائد الآلي الكاميرات المواجهة للطريق و الكان و نظام تحديد المواقع العالمي و تشمل تحديد الاتجاه ومقياس المغناطيسية وأجهزة الاستشعار الحرارية والأعطال وسجلات نظام التشغيل.
يتم تسجيل الكاميرا المواجهة للسائق فقط إذا قمت صراحة بالاشتراك في الإعدادات. لم يتم تسجيل الميكروفون.

باستخدام برنامج القائد الآلي ، فإنك توافق على [سياسة الخصوصية الخاصة بنا](https://comma.ai/privacy). أنت تدرك أن استخدام هذا البرنامج أو الخدمات المرتبطة به سيؤدي إلى إنشاء أنواع معينة من بيانات المستخدم ، والتي قد يتم تسجيلها وتخزينها وفقًا لتقدير كوما وحدها. بقبول هذه الاتفاقية, أنت تمنح حقًا عالميًا غير قابل للإلغاء ودائم لفاصلة لاستخدام هذه البيانات.

السلامة والاختبار
----

* القائد الآلي يراعي إرشادات ISO26262 ، انظر [السلامة](docs/SAFETY.md) لمزيد من التفاصيل.
* يحتوي برنامج القائد الآلي على برنامج في عقدة [الاختبارات](.github/workflows/selfdrive_tests.yaml) التي تعمل على كل التزام.
* الكود الذي يفرض تطبيق نموذج الأمان يعيش في الباندا ومكتوب بلغة C ، انظر [دقة كود](https://github.com/commaai/panda#code-rigor) لمزيد من التفاصيل.
* الباندا لديه برنامج في عقدة [اختبارات السلامة](https://github.com/commaai/panda/tree/master/tests/safety).
* داخليًا ، لدينا جهاز في مجموعة اختبار عقدة مسمترة الذي يبني العمليات المختلفة ويختبرها.
* الباندا لديها أجهزة إضافية في العقدة [الاختبارات](https://github.com/commaai/panda/blob/master/Jenkinsfile).
* نقوم بتشغيل أحدث برنامج القائد الآلي في خزانة اختبار تحتوي على 10 أجهزة كوما تعيد تشغيل المسارات باستمرار.

بنية الدليل
------
    .
    ├── cereal              # مواصفات الرسائل و الطبقات المستخدمة في جميع الخوارزميات
    ├── common              # مكتبة مثل الوظائف التي قمنا بتطويرها هنا
    ├── docs                # التوثيق
    ├── opendbc             # ملفات توضح كيفية تفسير البيانات من السيارات
    ├── panda               # رمز يستخدم للتواصل على الكان
    ├── third_party         # مكتبات خارجية
    ├── pyextra             # حزم بايثون الإضافية
    └── selfdrive           # الأكواد المطلوبة لقيادة السيارة
        ├── assets          # الخطوط, الصور, و الأصوات للواجهة
        ├── athena          # يسمح بالتواصل مع التطبيق
        ├── boardd          # الديمون الذي يسمح للاتصال مع البورد
        ├── camerad         # يسمح لالتقاط الصور من مستشعرات الكاميرا
        ├── car             # رمز السيارة المحدد لقراءة الحالات والتحكم في المشغلات
        ├── common          # كود C / C ++ مشترك الدومين
        ├── controls        # التخطيط والضوابط
        ├── debug           # أدوات لمساعدتك على التصحيح والقيام بمنافذ السيارة
        ├── locationd       # توطين دقيق وتقدير معايرة السيارة
        ├── logcatd         # ملفات الأندرويد والخدمات
        ├── loggerd         # مسجل وتحميل بيانات السيارة
        ├── modeld          # نظام مراقبة القيادة أثناء العمل
        ├── proclogd        # معلومات السجلات من proc
        ├── sensord         # رمز واجهة تحديد الاتجاه
        ├── test            # اختبارات الوحدة واختبارات النظام وجهاز محاكاة السيارة
        └── ui              # واجهة المستخدم

الترخيص
------

تم إصدار القائد الآلي بموجب ترخيص MIT. تم إصدار بعض أجزاء البرنامج بموجب تراخيص أخرى كما هو محدد.
يجب على أي مستخدم لهذا البرنامج تعويض كوما للذكاء الاصطناهي. ومديريها ومسؤوليها وموظفيها ووكلائها وحاملي الأسهم والشركات التابعة لها والمقاولين من الباطن والعملاء وضد جميع الادعاءات والمطالبات والإجراءات والدعاوى والمطالب والأضرار والمسؤوليات. والالتزامات والخسائر والتسويات والأحكام والتكاليف والنفقات (بما في ذلك على سبيل المثال لا الحصر أتعاب المحاماة والتكاليف) التي تنشأ عن أو تتعلق أو تنتج عن أي استخدام لهذا البرنامج من قبل المستخدم.

**هذا هو برنامج ألفا عالي الجودة لأغراض البحث فقط. هذا ليس منتج.
أنت مسؤول عن الامتثال للقوانين واللوائح المحلية.
لا صراحة أو ضمنا الضمان.**

---

<img src="https://d1qb2nb5cznatu.cloudfront.net/startups/i/1061157-bc7e9bf3b246ece7322e6ffe653f6af8-medium_jpg.jpg?buster=1458363130" width="75"></img> <img src="https://cdn-images-1.medium.com/max/1600/1*C87EjxGeMPrkTuVRVWVg4w.png" width="225"></img>

[![openpilot tests](https://github.com/commaai/openpilot/workflows/openpilot%20tests/badge.svg?event=push)](https://github.com/commaai/openpilot/actions)
[![Total alerts](https://img.shields.io/lgtm/alerts/g/commaai/openpilot.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/commaai/openpilot/alerts/)
[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/commaai/openpilot.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/commaai/openpilot/context:python)
[![Language grade: C/C++](https://img.shields.io/lgtm/grade/cpp/g/commaai/openpilot.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/commaai/openpilot/context:cpp)
[![codecov](https://codecov.io/gh/commaai/openpilot/branch/master/graph/badge.svg)](https://codecov.io/gh/commaai/openpilot)
