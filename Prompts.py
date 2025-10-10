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
whisperPromptGenericJA = "みなさん、おはようございます！今日もラジオを聴いてくれてありがとうございます。今日の天気は晴れ、気持ちのいい一日になりそうですね。リスナーさんから「最近おすすめの本はありますか？」という質問が届いています。"
whisperPromptGenericKO = "안녕하세요, 오늘도 여러분의 하루를 함께하는 라디오 푸른하늘입니다.지금 시각은 오후 두 시를 막 지나고 있습니다.잠시 후에는 여러분의 사연과 함께하는 ‘마음의 소리’ 코너가 이어집니다.한 청취자분이 이런 말을 남기셨어요. “작은 위로가 큰 힘이 될 때가 있더라고요.”"

translationStyle = "Try to preserve the original tone of voice and nuances of the words where possible. "
translationContextClarisSeason3 = ("For context, "
                      "クラリス (ClariS) are a trio of singers comprising of クララ (Clara), エリイ (Elly), and アンナ (Anna). "
                      "One of their songs is 海月 (Umitsuki), also written as うみつき (Umitsuki). "
                      + translationStyle)
translationContextClarisSeason2 = ("For context, "
                      "クラリス (ClariS) are a duo of singers comprising of クララ (Clara) and カレン (Karen). "
                      "They recently held live tours named ティンクトゥラ (Tinctura) and ヴィア・フォルトゥナ (Via Fortuna). "
                      + translationStyle)
translationContextMizukiNana = ("For context, "
                      "水樹 奈々 (みずき なな) (Mizuki Nana) is a J-pop singer. "
                      "She hosts a radio show called スマイルギャング (Smile Gang, sometimes abbreviated to スマギャン) with 福圓 美里 (ふくえん みさと) (Misato Fukuen). "
                      + translationStyle)
translationContextBlueArchive = ("For context, "
                                 "This is a live broadcast about the game Blue Archive. "
                                 + translationStyle)
# translationContext = "For context, バンドリ (bandori) is the abbreviation for the BanG Dream! franchise."
