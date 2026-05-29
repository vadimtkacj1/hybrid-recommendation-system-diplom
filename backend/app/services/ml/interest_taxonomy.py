from __future__ import annotations

INTEREST_LABEL_TEXTS: dict[str, str] = {
    "Film & Animation": (
        "Film and animation movies cinema cartoons short films animated series "
        "кино мультфільм анімація фільм"
    ),
    "Music": (
        "Music songs albums playlists artists bands singers concerts clips "
        "музика пісня кліп альбом"
    ),
    "Pets & Animals": (
        "Pets animals dogs cats wildlife cute animals nature veterinary "
        "тварини собаки коти"
    ),
    "Sports": (
        "Sports football soccer basketball tennis matches athletes highlights "
        "спорт футбол матч чемпіонат"
    ),
    "Travel & Events": (
        "Travel tourism trips adventure vacation world explore vlog travel guide "
        "подорож подорожі туризм"
    ),
    "Gaming": (
        "Gaming games gameplay walkthrough esports minecraft streamer twitch let play "
        "ігри геймінг стрім геймплей виживання sandbox"
    ),
    "People & Blogs": (
        "People and blogs lifestyle vlog daily life personal stories blogger "
        "блог влог життя люди"
    ),
    "Comedy": (
        "Comedy humor funny jokes sketch stand up parody memes laughs "
        "комедія гумор приколи жарти ліга сміху смех юмор шоу"
    ),
    "Entertainment": (
        "Entertainment shows talk show celebrity gossip highlights pop culture "
        "розваги шоу інтерв'ю зірки естрада"
    ),
    "News & Politics": (
        "News politics government elections world affairs analysis economy war "
        "новини політика світ"
    ),
    "How-to & Style": (
        "How to tutorial DIY fashion beauty cooking recipes tips life hacks craft "
        "як зробити урок майстер-клас рецепт"
    ),
    "Education": (
        "Education learning lectures courses school university study science lessons "
        "освіта навчання лекція курс університет"
    ),
    "Science & Technology": (
        "Science technology programming software engineering AI machine learning IT "
        "tutorial code developer java python n8n automation "
        "наука технології програмування"
    ),
    "Anime/Animation": (
        "Anime manga japanese animation series episode fantasy isekai otaku "
        "аніме манга серія"
    ),
}

INTEREST_CATEGORY_ORDER: tuple[str, ...] = tuple(INTEREST_LABEL_TEXTS.keys())
