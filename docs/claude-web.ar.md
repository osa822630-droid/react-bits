# استخدام React Bits مع Claude Web

الإضافة دي معمولة لمحادثات Claude على الويب؛ مش محتاجة Claude Code ولا MCP محلي ولا مفتاح API.

## الإضافة من الـMarketplace

1. افتح [Claude](https://claude.ai) وسجّل دخولك.
2. من **Customize** افتح **Plugins**، ثم **Add → Add marketplace → Add from a repository**.
3. اكتب اسم الريبو ده أو رابطه، واضغط **Add** أو **Sync**:

   ```text
   osa822630-droid/react-bits
   ```

   الرابط الكامل: `https://github.com/osa822630-droid/react-bits`.

4. إضافة الـmarketplace بتضيف قائمة الإضافات بس. افتح **Discover**، واختار **React Bits** واضغط **Add** عشان تثبّت الـplugin نفسه.
5. ابدأ شات جديد، واكتب مثلاً: «استخدم React Bits واعمل عنوان متحرك بـ SplitText» أو «اقترح خلفية متحركة لصفحة React». ممكن كمان تكتب `/` وتختار مهارة React Bits من القائمة.

لو Claude طلب تفعيل تنفيذ الكود، فعّل **Create and edit files** (أو **Code execution and file creation**) من **Settings → Capabilities**. أسماء القوائم وإتاحة الميزات ممكن تختلف حسب الحساب.

## الإضافة بتعمل إيه؟

- بتبحث في كتالوج المكونات المرفق، وتعرف النوع والوصف والنسخ المتاحة والـdependencies لكل نسخة.
- لما تحتاج الكود، بتقرأ ملف الـregistry من فرع `main` للريبو ده على GitHub، ولو تعذّر الوصول إليه بتحاول الـregistry الرسمي لـ React Bits. الشبكة مطلوبة لجلب السورس؛ طلب الشبكة بيحتوي على اسم المكون ونسخته فقط، مش محتوى المحادثة أو ملفات مشروعك.
- لو الشبكة أو تنفيذ الكود مش متاحين، تقدر تقترح مكونات وتديك رابط التوثيق أو أمر التثبيت. ولو محتاج الكود الدقيق، ارفع ملف الـregistry أو سورس المكون للشات.
- دعم معاينة الـArtifacts بيعتمد على المكتبات والـCSS وواجهات المتصفح المتاحة هناك؛ مش كل مكون يشتغل في المعاينة من غير تهيئة.

مكونات React Bits خاضعة لترخيص الريبو [MIT + Commons Clause](../LICENSE.md)، بما فيه القيود على إعادة توزيع المكونات. الإضافة نفسها مش بتغيّر الترخيص.

## لو الإضافة مش ظاهرة أو مش بتتحدّث

- اتأكد إن ملفات `.claude-plugin/marketplace.json` و`plugins/react-bits/` موجودة على **الفرع الافتراضي** للريبو على GitHub. التغييرات المحلية مش بتظهر في Claude قبل نشرها.
- بعد إضافة الـmarketplace، لازم تثبّت **React Bits** من **Discover** كخطوة منفصلة. لو كان الـmarketplace مضاف قبل التحديث، استخدم **Check for updates** أو **Sync automatically**.
- لو ظهرت مشكلة اسم marketplace مكرر، شيل النسخة القديمة من قائمة الـmarketplaces وحاول تضيفها تاني. لو الريبو بقى private، اربط GitHub واسمح لتطبيق Claude بالوصول له عند الطلب.
- اتأكد إن المهارة مفعّلة، وجرّب تختارها من قائمة `/` أو اذكر «React Bits» صراحةً في طلبك.

## تحديث الكتالوج للمطورين

بعد تعديل مكونات أو ملفات الـregistry، شغّل من جذر الريبو:

```bash
npm run registry:build
npm run claude:catalog
npm run test:claude
```

احفظ التغييرات الناتجة مع الكود، وزوّد رقم النسخة بنفس القيمة في `.claude-plugin/marketplace.json` و`plugins/react-bits/.claude-plugin/plugin.json` عند نشر تحديث للـplugin. `npm run claude:catalog:check` بيتأكد إن نسخة الكتالوج المرفقة محدثة من غير تعديلها.
