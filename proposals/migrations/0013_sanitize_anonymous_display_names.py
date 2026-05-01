import re
from django.db import migrations

# 0012 と同一（連結「形容詞名詞」CamelCase は廃止方針のため除去）
_LEGACY_ANIMALS = [
    "Antelope", "Badger", "Bat", "Beaver", "Bison", "Boar", "Buffalo", "Camel", "Caribou", "Cat",
    "Cobra", "Cougar", "Coyote", "Crane", "Crow", "Deer", "Dog", "Donkey", "Duck", "Elk",
    "Falcon", "Ferret", "Frog", "Gazelle", "Gecko", "Goat", "Goose", "Gorilla", "Heron", "Horse",
    "Hyena", "Jaguar", "Koala", "Lemur", "Llama", "Lynx", "Magpie", "Mink", "Moose", "Ocelot",
    "Otter", "Owl", "Panda", "Parrot", "Peacock", "Penguin", "Puma", "Rabbit", "Raccoon", "Raven",
    "Seal", "Sheep", "Skunk", "Sparrow", "Swan", "Tapir", "Toucan", "Turkey", "Turtle", "Viper",
]
_LEGACY_PLANTS = [
    "Alder", "Anise", "Ash", "Aspen", "Basil", "Beech", "Begonia", "Bluebell", "Camellia", "Carnation",
    "Cedar", "Cherry", "Chive", "Clover", "Cypress", "Daffodil", "Dahlia", "Daisy", "Elm", "Fennel",
    "Fig", "Fir", "Gardenia", "Geranium", "Ginkgo", "Heather", "Hibiscus", "Holly", "Hyacinth", "Iris",
    "Jasmine", "Juniper", "Lavender", "Lilac", "Linden", "Lotus", "Magnolia", "Maple", "Marigold", "Mint",
    "Myrtle", "Nettle", "Oleander", "Olive", "Orchid", "Palm", "Peony", "Poppy", "Primrose", "Rosemary",
    "Sage", "Spruce", "Sunflower", "Thyme", "Tulip", "Violet", "Walnut", "Willow", "Yarrow", "Yew",
]
_LEGACY_ADJECTIVES = [
    "Amber", "Arctic", "Autumn", "Azure", "Bright", "Calm", "Clear", "Crimson", "Dawn", "Deep",
    "Emerald", "Frost", "Golden", "Grand", "Green", "Indigo", "Ivory", "Jade", "Lunar", "Maple",
    "Misty", "Noble", "Ocean", "Olive", "Pearl", "Quiet", "Rapid", "Royal", "Ruby", "Sable",
    "Sandy", "Scarlet", "Silver", "Silent", "Sky", "Solar", "Spring", "Stone", "Summer", "Swift",
]

_BAD_NUMERIC = re.compile(r"^(Animal|Plant|Inorganic)\d{3}$")


def _legacy_compound_names():
    out = set()
    for adj in _LEGACY_ADJECTIVES:
        for w in _LEGACY_ANIMALS + _LEGACY_PLANTS:
            out.add(f"{adj}{w}")
    return out


_COMPOUND_BAD = None


def _legacy_pattern_bad(name: str) -> bool:
    global _COMPOUND_BAD
    if _BAD_NUMERIC.match(name):
        return True
    if _COMPOUND_BAD is None:
        _COMPOUND_BAD = _legacy_compound_names()
    return name in _COMPOUND_BAD


_ANIMALS = [
    "Antelope", "Badger", "Bat", "Beaver", "Bison", "Boar", "Buffalo", "Camel", "Caribou", "Cat",
    "Cobra", "Cougar", "Coyote", "Crane", "Crow", "Deer", "Dog", "Donkey", "Duck", "Elk",
    "Falcon", "Ferret", "Frog", "Gazelle", "Gecko", "Goat", "Goose", "Gorilla", "Heron", "Horse",
    "Hyena", "Jaguar", "Koala", "Lemur", "Llama", "Lynx", "Magpie", "Mink", "Moose", "Ocelot",
    "Otter", "Owl", "Panda", "Parrot", "Peacock", "Penguin", "Puma", "Rabbit", "Raccoon", "Raven",
    "Seal", "Sheep", "Skunk", "Sparrow", "Swan", "Tapir", "Toucan", "Turkey", "Turtle", "Viper",
    "Lion", "Tiger", "Bear", "Wolf", "Fox", "Eagle", "Hawk", "Dolphin", "Whale", "Shark",
    "Panther", "Leopard", "Cheetah", "Hedgehog", "Wombat", "Zebra",
]

_PLANTS = [
    "Alder", "Anise", "Ash", "Aspen", "Basil", "Beech", "Begonia", "Bluebell", "Camellia", "Carnation",
    "Cedar", "Cherry", "Chive", "Clover", "Cypress", "Daffodil", "Dahlia", "Daisy", "Elm", "Fennel",
    "Fig", "Fir", "Gardenia", "Geranium", "Ginkgo", "Heather", "Hibiscus", "Holly", "Hyacinth", "Iris",
    "Jasmine", "Juniper", "Lavender", "Lilac", "Linden", "Lotus", "Magnolia", "Maple", "Marigold", "Mint",
    "Myrtle", "Nettle", "Oleander", "Olive", "Orchid", "Palm", "Peony", "Poppy", "Primrose", "Rose",
    "Rosemary", "Sage", "Spruce", "Sunflower", "Thyme", "Tulip", "Walnut", "Willow", "Yarrow", "Yew",
    "Bamboo", "Fern", "Moss", "Sakura", "Lily", "Violet",
]

# 具象名のみ（動・植）。色名に依存せず多様な形容詞（単語）を使用。
_ADJECTIVES = [
    "Naughty", "Patient", "Impatient", "Cheerful", "Brave", "Calm", "Lively", "Gentle", "Bold", "Timid",
    "Swift", "Quiet", "Loud", "Bright", "Misty", "Noble", "Curious", "Wise", "Playful", "Serious",
    "Happy", "Humble", "Proud", "Kind", "Clever", "Loyal", "Wild", "Tame", "Sunny", "Stormy",
    "Eager", "Lazy", "Fierce", "Merry", "Jolly", "Brisk", "Steady", "Peppy", "Sleepy", "Fuzzy",
    "Spry", "Daring", "Hasty", "Cozy", "Icy", "Earnest", "Hushed", "Rustic", "Urban", "Fleet",
]


def _build_canonical_items():
    """(name, category) category は animal | plant のみ。"""
    items = []

    seen = set()
    for n in _ANIMALS:
        pair = (n, "animal")
        if n not in seen:
            seen.add(n)
            items.append(pair)
    for n in _PLANTS:
        pair = (n, "plant")
        if n not in seen:
            seen.add(n)
            items.append(pair)
    for adj in _ADJECTIVES:
        for n in _ANIMALS:
            key = f"{adj}-{n}"
            if key not in seen:
                seen.add(key)
                items.append((key, "animal"))
        for n in _PLANTS:
            key = f"{adj}-{n}"
            if key not in seen:
                seen.add(key)
                items.append((key, "plant"))
    # プール枯渇時のフォールバック表示（割当ロジック専用。通常プールからは選ばない）
    if "Anonymous" not in seen:
        seen.add("Anonymous")
        items.append(("Anonymous", "animal"))
    allowed = {n for (n, _) in items}
    canon_cat = dict(items)
    return items, allowed, canon_cat


def _name_taken(AnonymousName, name: str, exclude_pk=None):
    qs = AnonymousName.objects.filter(name=name)
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()


def _sanitize_and_seed(apps, schema_editor):
    AnonymousName = apps.get_model("proposals", "AnonymousName")
    ChallengeUserAnonymousName = apps.get_model("selections", "ChallengeUserAnonymousName")
    Proposal = apps.get_model("proposals", "Proposal")

    pool_items, allowed_names, canon_cat = _build_canonical_items()
    pool_index = [0]

    def allocate_new_name(exclude_pk=None):
        for _ in range(len(pool_items) * 3):
            candidate_name, _ = pool_items[pool_index[0] % len(pool_items)]
            pool_index[0] += 1
            if not _name_taken(AnonymousName, candidate_name, exclude_pk):
                return candidate_name, canon_cat[candidate_name]
        raise RuntimeError("anonymous name pool exhausted during migration 0013")

    def row_needs_migration(an) -> bool:
        if _legacy_pattern_bad(an.name):
            return True
        if an.category == "inorganic":
            return True
        if an.name not in allowed_names:
            return True
        if canon_cat.get(an.name) != an.category:
            return True
        return False

    for an in list(AnonymousName.objects.all()):
        if an.name == "Anonymous":
            if an.category != "animal":
                an.category = "animal"
                an.save(update_fields=["category"])
            continue
        if not row_needs_migration(an):
            continue
        in_use = (
            ChallengeUserAnonymousName.objects.filter(anonymous_name_id=an.pk).exists()
            or Proposal.objects.filter(anonymous_name_id=an.pk).exists()
        )
        if not in_use:
            an.delete()
            continue
        new_name, new_cat = allocate_new_name(exclude_pk=an.pk)
        an.name = new_name
        an.category = new_cat
        an.save(update_fields=["name", "category"])

    # 許可セット外・無機カテゴリの行を未使用のみ削除（上で参照中は改名済み）
    for an in list(
        AnonymousName.objects.filter(category="inorganic")
        | AnonymousName.objects.exclude(name__in=allowed_names)
    ):
        if an.name not in allowed_names or an.category == "inorganic":
            in_use = (
                ChallengeUserAnonymousName.objects.filter(anonymous_name_id=an.pk).exists()
                or Proposal.objects.filter(anonymous_name_id=an.pk).exists()
            )
            if not in_use:
                an.delete()

    # 表示の一貫性：許可セット内でも category が違えば是正
    for an in AnonymousName.objects.filter(name__in=allowed_names):
        expect = canon_cat.get(an.name)
        if expect and an.category != expect:
            an.category = expect
            an.save(update_fields=["category"])

    for name, category in pool_items:
        AnonymousName.objects.get_or_create(name=name, defaults={"category": category})


def noop_reverse(apps, schema_editor):
    return


class Migration(migrations.Migration):
    dependencies = [
        ("proposals", "0012_ensure_300_animal_plant_names"),
        ("selections", "0002_challengeuseranonymousname"),
    ]

    operations = [
        migrations.RunPython(_sanitize_and_seed, noop_reverse),
    ]
