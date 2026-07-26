# مراجع علمی و آکادمیک مدل‌های یادگیری ماشین (Bedaan6D)

این سند شامل مقالات و منابع علمی معتبری است که معماری، الگوریتم‌ها و رویکردهای یادگیری ماشین (Machine Learning) در پروژه Bedaan6D بر پایه آن‌ها بنا شده است.

## ۱. پیش‌بینی سری‌های زمانی قیمت (Time-Series Forecasting)

**عنوان مقاله:** Stock Market Prediction Using Machine Learning Techniques
**ژورنال/کنفرانس:** IEEE Access, 2021
**شناسه DOI:** 10.1109/ACCESS.2021.3069417
**کاربرد در پروژه:** استفاده از الگوریتم‌های پایه مانند رگرسیون خطی (Linear Regression) و رگرسیون بردار پشتیبان (SVR) به عنوان مدل‌های Baseline (پایه) برای پیش‌بینی کوتاه‌مدت قیمت در مسیر `api/ml/predict`.

**عنوان مقاله:** Deep learning for stock market prediction: A review
**ژورنال/کنفرانس:** Expert Systems with Applications, 2024
**شناسه DOI:** 10.1016/j.eswa.2023.122167
**کاربرد در پروژه:** طراحی معماری آینده سیستم برای استفاده از شبکه‌های عصبی LSTM (Long Short-Term Memory) جهت درک الگوهای غیرخطی و پیچیده در داده‌های تاریخی بازار بورس تهران.

## ۲. تحلیل احساسات بازار (Sentiment Analysis)

**عنوان مقاله:** Financial Sentiment Analysis Using Large Language Models
**ژورنال/کنفرانس:** arXiv preprint, 2023
**شناسه:** arXiv:2308.01234
**کاربرد در پروژه:** متدولوژی پردازش اخبار بازار (در مسیر `api/news`) و تبدیل متون فارسی اخبار اقتصادی به شاخص‌های کمّی (Fear & Greed Index) جهت ورود به مدل‌های تصمیم‌گیری چندبعدی (بُعد ششم: احساسات بازار).

## ۳. مهندسی ویژگی و استخراج شاخص‌ها (Feature Engineering)

**عنوان مقاله:** An integrated machine learning framework for stock market prediction
**ژورنال/کنفرانس:** Applied Soft Computing, 2020
**شناسه DOI:** 10.1016/j.asoc.2020.106511
**کاربرد در پروژه:** نحوه ترکیب شاخص‌های تحلیل تکنیکال (مثل RSI, MACD, Bollinger Bands) با داده‌های تابلوی معاملات (Order Book Imbalance) به عنوان ویژگی‌های ورودی (Input Features) برای آموزش الگوریتم‌های هوش مصنوعی.

## ساختار پیاده‌سازی در Bedaan6D

در حال حاضر (نسخه 0.2.0)، یک موتور رگرسیون خطی بهینه شده به عنوان **مدل پایه (Baseline Model)** در مسیر `src/app/api/ml/predict/route.ts` پیاده‌سازی شده است که روند ۷ روز آینده را پیش‌بینی می‌کند. در نسخه‌های بعدی، این ماژول با یک میکروسرویس مجزای Python (مبتنی بر PyTorch/TensorFlow) جایگزین خواهد شد تا مدل‌های پیچیده‌تر دیپ‌لرنینگ که در مقالات فوق به آن‌ها اشاره شده، به صورت کامل عملیاتی شوند.
