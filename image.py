import telebot
import aiohttp
import asyncio
from deep_translator import GoogleTranslator
from keep_alive import keep_alive

keep_alive()

token = "7747612730:AAGYLOVFz02DyA-6LGGaH9RXl3HmxmyISHE"
bot = telebot.TeleBot(token)

# زر "Start"
@bot.message_handler(commands=['start'])
def send_welcome(message):
    # رسالة ترحيب بعد تعديلها
    bot.send_message(
        message.chat.id, 
        "💬 مرحباً بك في بوت التحويل إلى صور! 🎨\n\n" 
        "أرسل لي النص بأي لغة وسأقوم بتحويله إلى صورة!\n\n"
        "تم تطوير البوت بواسطة [@Cornerdzz]", 
        parse_mode='Markdown'  # استخدام Markdown لتنسيق النصوص
    )

# دالة لتحويل النص إلى صورة باستخدام API
async def generate_image_async(message):
    user_input = message.text
    
    # ترجمة النص إلى الإنجليزية باستخدام deep_translator
    translated_text = GoogleTranslator(source='auto', target='en').translate(user_input)
    
    # إعداد الترويسات للمطالبة بـ API
    headers = {
        'authority': 'www.blackbox.ai',
        'accept': '/',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/json',
        'origin': 'https://www.blackbox.ai',
        'referer': 'https://www.blackbox.ai/agent/ImageGenerationLV45LJp',
        'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36',
    }

    # البيانات التي سيتم إرسالها إلى API
    json_data = {
        'messages': [
            {
                'id': 'BInlT_BidR17C9Q9LuxPP',
                'content': translated_text,
                'role': 'user',
            },
        ],
        'id': 'BInlT_BidR17C9Q9LuxPP',
        'previewToken': None,
        'userId': None,
        'codeModelMode': True,
        'agentMode': {
            'mode': True,
            'id': 'ImageGenerationLV45LJp',
            'name': 'Image Generation',
        },
        'isMicMode': False,
        'maxTokens': 1024,
        'validated': '00f37b34-a166-4efb-bce5-1312d87f2f94',
    }

    async with aiohttp.ClientSession() as session:
        async with session.post('https://www.blackbox.ai/api/chat', headers=headers, json=json_data) as response:
            rr = await response.text()
            print(rr)
            
            # معالجة الاستجابة
            parts = rr.split('(')
            if len(parts) > 1:
                link = parts[1].split(')')[0]
                return link
            else:
                return None

# دالة لإرسال الصورة إذا تم تحويل النص بنجاح
async def send_first_successful_request(message):
    # محاولة واحدة فقط للحصول على الصورة بسرعة
    result = await generate_image_async(message)
    
    if result:
        # إرسال الصورة مع رابط حساب المطور في خانة النص
        bot.send_photo(
            message.chat.id, 
            result, 
            caption="تم عبر [@Cornerdzz]", 
            parse_mode='Markdown'  # استخدام Markdown لعرض الرابط بشكل صحيح
        )
    else:
        bot.reply_to(message, "لا يوجد رابط في النص. حاول إرسال نص آخر.")

# التعامل مع الرسائل
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    # تشغيل الدالة غير المتزامنة باستخدام asyncio
    asyncio.run(send_first_successful_request(message))

# تشغيل البوت بشكل مستمر
while True:
    try:
        print("🚀 يتم تشغيل البوت...")
        bot.polling(non_stop=True)  # تشغيل البوت بدون توقف
    except Exception as e:
        print(f"⚠️ حدث خطأ: {e}. إعادة تشغيل البوت بعد 5 ثوانٍ.")
