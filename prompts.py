# keywordsClaris = ["クララ", "エリイ", "アンナ", "リスアニ"]
# keywordsBandori = ["バンドリ", "愛美", "伊藤彩沙", "大橋彩香", "西本りみ", "大塚紗英"]
# translationsBandori = {
#     "バンドリ": "bandori",
#     "アイミ": "Aimi",
#     "愛美": "Aimi",
# }
# prompts can help teach whisper unknown words/spellings
# whisperPrompt = "。".join(keywordsBandori)
# whisperPrompt = "これはトークショーです。クラリスについてです。3人はクララとエリイとアンナです。最近、リスアニライブでパフォーマンスしました。" #ウミツキ。ウミツキ as Umitsuki
# whisperPrompt = "ClariSは3人組のグループです。メンバーはクララ、エリー、アンナです。これは「Umitsuki」というラジオ番組です。"
# whisperPrompt = "クラリスは、クララとカレンの2人で構成されたアニソンデュオです。デビュー当初から顔を出さずに活動し、ミステリアスな存在として注目を集めてきました。透き通るような歌声とキャッチーなメロディーで、多くのアニメファンに愛されています。クララは柔らかく透明感のある声質を持ち、カレンはしっかりと芯のある歌声が特徴です。2人のハーモニーは絶妙で、楽曲ごとに異なる世界観を見事に表現しています。"
whisperPromptGeneric = "みなさん、おはようございます！今日もラジオを聴いてくれてありがとうございます。今日の天気は晴れ、気持ちのいい一日になりそうですね。リスナーさんから「最近おすすめの本はありますか？」という質問が届いています。"

translationStyle = "Try to preserve the original tone of voice and nuances of the words where possible. "
translationContextClarisSeason3 = ("For context, "
                      "クラリス (ClariS) are trio of singers comprising of クララ (Clara), エリイ (Elly), and アンナ (Anna). "
                      "One of their songs is 海月 (Umitsuki), also written as うみつき (Umitsuki). "
                      + translationStyle)
translationContextClarisSeason2 = ("For context, "
                      "クラリス (ClariS) are duo of singers comprising of クララ (Clara) and カレン (Karen). "
                      "They recently held live tours named ティンクトゥラ (Tinctura) and ヴィア・フォルトゥナ (Via Fortuna). "
                      + translationStyle)
translationContextMizukiNana = ("For context, "
                      "水樹 奈々 (みずき なな) (Mizuki Nana) is a J-pop singer. "
                      "She hosts a radio show called スマイルギャング (Smile Gang, sometimes abbreviated to スマギャン) with 福圓 美里 (ふくえん みさと) (Misato Fukuen). "
                      + translationStyle)
# translationContext = "For context, バンドリ (bandori) is the abbreviation for the BanG Dream! franchise."
