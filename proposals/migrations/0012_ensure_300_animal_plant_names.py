from django.db import migrations


ANIMALS = [
    "Antelope", "Badger", "Bat", "Beaver", "Bison", "Boar", "Buffalo", "Camel", "Caribou", "Cat",
    "Cobra", "Cougar", "Coyote", "Crane", "Crow", "Deer", "Dog", "Donkey", "Duck", "Elk",
    "Falcon", "Ferret", "Frog", "Gazelle", "Gecko", "Goat", "Goose", "Gorilla", "Heron", "Horse",
    "Hyena", "Jaguar", "Koala", "Lemur", "Llama", "Lynx", "Magpie", "Mink", "Moose", "Ocelot",
    "Otter", "Owl", "Panda", "Parrot", "Peacock", "Penguin", "Puma", "Rabbit", "Raccoon", "Raven",
    "Seal", "Sheep", "Skunk", "Sparrow", "Swan", "Tapir", "Toucan", "Turkey", "Turtle", "Viper",
]

PLANTS = [
    "Alder", "Anise", "Ash", "Aspen", "Basil", "Beech", "Begonia", "Bluebell", "Camellia", "Carnation",
    "Cedar", "Cherry", "Chive", "Clover", "Cypress", "Daffodil", "Dahlia", "Daisy", "Elm", "Fennel",
    "Fig", "Fir", "Gardenia", "Geranium", "Ginkgo", "Heather", "Hibiscus", "Holly", "Hyacinth", "Iris",
    "Jasmine", "Juniper", "Lavender", "Lilac", "Linden", "Lotus", "Magnolia", "Maple", "Marigold", "Mint",
    "Myrtle", "Nettle", "Oleander", "Olive", "Orchid", "Palm", "Peony", "Poppy", "Primrose", "Rosemary",
    "Sage", "Spruce", "Sunflower", "Thyme", "Tulip", "Violet", "Walnut", "Willow", "Yarrow", "Yew",
]

ADJECTIVES = [
    "Amber", "Arctic", "Autumn", "Azure", "Bright", "Calm", "Clear", "Crimson", "Dawn", "Deep",
    "Emerald", "Frost", "Golden", "Grand", "Green", "Indigo", "Ivory", "Jade", "Lunar", "Maple",
    "Misty", "Noble", "Ocean", "Olive", "Pearl", "Quiet", "Rapid", "Royal", "Ruby", "Sable",
    "Sandy", "Scarlet", "Silver", "Silent", "Sky", "Solar", "Spring", "Stone", "Summer", "Swift",
]


def ensure_300_names(apps, schema_editor):
    AnonymousName = apps.get_model("proposals", "AnonymousName")

    # まずは単語単体の名前を投入（読みやすい短名を優先）
    for animal in ANIMALS:
        AnonymousName.objects.get_or_create(name=animal, defaults={"category": "animal"})
    for plant in PLANTS:
        AnonymousName.objects.get_or_create(name=plant, defaults={"category": "plant"})

    # 不足分は英語の形容詞 + 動植物名で補完
    # 例: "AmberFalcon", "SilentMaple"
    def fill_category(target_category, base_words):
        current_count = AnonymousName.objects.count()
        if current_count >= 300:
            return
        for adj in ADJECTIVES:
            for word in base_words:
                name = f"{adj}{word}"
                AnonymousName.objects.get_or_create(
                    name=name,
                    defaults={"category": target_category},
                )
                current_count = AnonymousName.objects.count()
                if current_count >= 300:
                    return

    fill_category("animal", ANIMALS)
    fill_category("plant", PLANTS)


def noop_reverse(apps, schema_editor):
    return


class Migration(migrations.Migration):
    dependencies = [
        ("proposals", "0011_expand_anonymous_names_pool"),
    ]

    operations = [
        migrations.RunPython(ensure_300_names, noop_reverse),
    ]

