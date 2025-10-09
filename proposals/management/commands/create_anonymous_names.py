#!/usr/bin/env python
"""
匿名化用の名前データを作成するDjango管理コマンド
動物、植物、無機物の名前を500個投入
"""

from django.core.management.base import BaseCommand
from proposals.models import AnonymousName


class Command(BaseCommand):
    help = '匿名化用の名前データを作成する'

    def handle(self, *args, **options):
        """匿名名データを作成"""
        
        # 動物名（170個）
        animal_names = [
            'Lion', 'Tiger', 'Elephant', 'Giraffe', 'Zebra', 'Rhino', 'Hippo', 'Cheetah', 'Leopard', 'Panther',
            'Bear', 'Wolf', 'Fox', 'Deer', 'Rabbit', 'Squirrel', 'Chipmunk', 'Raccoon', 'Otter', 'Beaver',
            'Eagle', 'Hawk', 'Falcon', 'Owl', 'Parrot', 'Peacock', 'Flamingo', 'Swan', 'Duck', 'Goose',
            'Shark', 'Whale', 'Dolphin', 'Octopus', 'Jellyfish', 'Starfish', 'Seahorse', 'Turtle', 'Crab', 'Lobster',
            'Butterfly', 'Bee', 'Ant', 'Spider', 'Dragonfly', 'Ladybug', 'Grasshopper', 'Cricket', 'Firefly', 'Caterpillar',
            'Snake', 'Lizard', 'Frog', 'Toad', 'Salamander', 'Gecko', 'Iguana', 'Chameleon', 'Python', 'Cobra',
            'Cat', 'Dog', 'Horse', 'Cow', 'Pig', 'Sheep', 'Goat', 'Chicken', 'Rooster', 'Duck',
            'Panda', 'Kangaroo', 'Koala', 'Platypus', 'Sloth', 'Armadillo', 'Anteater', 'Capybara', 'Llama', 'Alpaca',
            'Monkey', 'Ape', 'Gorilla', 'Chimpanzee', 'Orangutan', 'Baboon', 'Lemur', 'Marmoset', 'Gibbon', 'Bonobo',
            'Penguin', 'Seal', 'Walrus', 'Polar Bear', 'Arctic Fox', 'Snow Leopard', 'Reindeer', 'Moose', 'Elk', 'Bison',
            'Lynx', 'Bobcat', 'Cougar', 'Jaguar', 'Ocelot', 'Serval', 'Caracal', 'Mountain Lion', 'Puma', 'Cheetah',
            'Dolphin', 'Porpoise', 'Orca', 'Beluga', 'Narwhal', 'Blue Whale', 'Humpback', 'Sperm Whale', 'Killer Whale', 'Gray Whale',
            'Swordfish', 'Tuna', 'Salmon', 'Trout', 'Bass', 'Pike', 'Perch', 'Catfish', 'Cod', 'Haddock',
            'Angelfish', 'Clownfish', 'Guppy', 'Goldfish', 'Betta', 'Tetra', 'Danio', 'Barracuda', 'Piranha', 'Eel',
            'Hamster', 'Gerbil', 'Guinea Pig', 'Mouse', 'Rat', 'Ferret', 'Chinchilla', 'Hedgehog', 'Sugar Glider', 'Flying Squirrel',
            'Bat', 'Flying Fox', 'Vampire Bat', 'Fruit Bat', 'Microbat', 'Megabat', 'Free-tailed Bat', 'Leaf-nosed Bat', 'Horseshoe Bat', 'Long-eared Bat'
        ]
        
        # 植物名（170個）
        plant_names = [
            'Rose', 'Tulip', 'Daisy', 'Sunflower', 'Lily', 'Orchid', 'Carnation', 'Peony', 'Hydrangea', 'Azalea',
            'Cherry', 'Apple', 'Orange', 'Lemon', 'Lime', 'Grapefruit', 'Banana', 'Mango', 'Pineapple', 'Strawberry',
            'Oak', 'Maple', 'Pine', 'Cedar', 'Birch', 'Willow', 'Elm', 'Ash', 'Beech', 'Chestnut',
            'Bamboo', 'Palm', 'Cactus', 'Succulent', 'Fern', 'Moss', 'Lichen', 'Algae', 'Seaweed', 'Kelp',
            'Lavender', 'Sage', 'Thyme', 'Basil', 'Mint', 'Rosemary', 'Oregano', 'Parsley', 'Cilantro', 'Chives',
            'Tomato', 'Potato', 'Carrot', 'Onion', 'Garlic', 'Lettuce', 'Spinach', 'Broccoli', 'Cauliflower', 'Cabbage',
            'Corn', 'Wheat', 'Rice', 'Barley', 'Oats', 'Rye', 'Sorghum', 'Millet', 'Quinoa', 'Buckwheat',
            'Pea', 'Bean', 'Lentil', 'Chickpea', 'Soybean', 'Peanut', 'Almond', 'Walnut', 'Pecan', 'Hazelnut',
            'Coffee', 'Tea', 'Cocoa', 'Vanilla', 'Cinnamon', 'Ginger', 'Turmeric', 'Cardamom', 'Clove', 'Nutmeg',
            'Grape', 'Peach', 'Pear', 'Plum', 'Apricot', 'Fig', 'Date', 'Coconut', 'Avocado', 'Papaya',
            'Mushroom', 'Truffle', 'Morel', 'Chanterelle', 'Porcini', 'Shiitake', 'Oyster', 'Enoki', 'Maitake', 'Reishi',
            'Pumpkin', 'Squash', 'Zucchini', 'Cucumber', 'Melon', 'Watermelon', 'Cantaloupe', 'Honeydew', 'Kiwi', 'Passionfruit',
            'Blueberry', 'Raspberry', 'Blackberry', 'Cranberry', 'Gooseberry', 'Elderberry', 'Mulberry', 'Huckleberry', 'Boysenberry', 'Loganberry',
            'Iris', 'Gladiolus', 'Snapdragon', 'Pansy', 'Violet', 'Forget-me-not', 'Poppy', 'Marigold', 'Petunia', 'Impatiens',
            'Geranium', 'Begonia', 'Fuchsia', 'Coleus', 'Caladium', 'Hosta', 'Daylily', 'Hemerocallis', 'Astilbe', 'Bleeding Heart',
            'Jasmine', 'Honeysuckle', 'Wisteria', 'Clematis', 'Morning Glory', 'Sweet Pea', 'Nasturtium', 'Cosmos', 'Zinnia', 'Salvia',
            'Mint', 'Catnip', 'Lemon Balm', 'Bee Balm', 'Bergamot', 'Echinacea', 'Yarrow', 'Chamomile', 'Calendula', 'Nasturtium'
        ]
        
        # 無機物名（160個）
        inorganic_names = [
            'Oxygen', 'Hydrogen', 'Nitrogen', 'Carbon', 'Iron', 'Gold', 'Silver', 'Copper', 'Zinc', 'Lead',
            'Aluminum', 'Titanium', 'Chrome', 'Nickel', 'Cobalt', 'Manganese', 'Silicon', 'Phosphorus', 'Sulfur', 'Chlorine',
            'Sodium', 'Potassium', 'Calcium', 'Magnesium', 'Barium', 'Strontium', 'Lithium', 'Rubidium', 'Cesium', 'Francium',
            'Fluorine', 'Bromine', 'Iodine', 'Astatine', 'Helium', 'Neon', 'Argon', 'Krypton', 'Xenon', 'Radon',
            'Mercury', 'Cadmium', 'Tin', 'Antimony', 'Bismuth', 'Polonium', 'Astatine', 'Radon', 'Francium', 'Radium',
            'Uranium', 'Plutonium', 'Thorium', 'Protactinium', 'Neptunium', 'Americium', 'Curium', 'Berkelium', 'Californium', 'Einsteinium',
            'Water', 'Ice', 'Steam', 'Salt', 'Sugar', 'Sand', 'Clay', 'Limestone', 'Marble', 'Granite',
            'Diamond', 'Graphite', 'Quartz', 'Feldspar', 'Mica', 'Hematite', 'Magnetite', 'Pyrite', 'Galena', 'Sphalerite',
            'Calcite', 'Aragonite', 'Gypsum', 'Halite', 'Fluorite', 'Apatite', 'Olivine', 'Pyroxene', 'Amphibole', 'Biotite',
            'Glass', 'Ceramic', 'Plastic', 'Rubber', 'Concrete', 'Cement', 'Steel', 'Bronze', 'Brass', 'Aluminum',
            'Silicon', 'Germanium', 'Arsenic', 'Selenium', 'Tellurium', 'Polonium', 'Astatine', 'Radon', 'Francium', 'Radium',
            'Coal', 'Oil', 'Gas', 'Petroleum', 'Natural Gas', 'Propane', 'Butane', 'Methane', 'Ethane', 'Ethylene',
            'Acetylene', 'Benzene', 'Toluene', 'Xylene', 'Naphthalene', 'Anthracene', 'Phenanthrene', 'Fluorene', 'Pyrene', 'Chrysene',
            'Ammonia', 'Nitric Acid', 'Sulfuric Acid', 'Hydrochloric Acid', 'Phosphoric Acid', 'Acetic Acid', 'Formic Acid', 'Oxalic Acid', 'Citric Acid', 'Tartaric Acid',
            'Sodium Chloride', 'Potassium Chloride', 'Calcium Carbonate', 'Magnesium Sulfate', 'Barium Sulfate', 'Lead Sulfide', 'Zinc Oxide', 'Titanium Dioxide', 'Aluminum Oxide', 'Iron Oxide',
            'Silicon Dioxide', 'Carbon Dioxide', 'Carbon Monoxide', 'Nitrogen Dioxide', 'Sulfur Dioxide', 'Hydrogen Sulfide', 'Ammonium Chloride', 'Sodium Hydroxide', 'Potassium Hydroxide', 'Calcium Hydroxide'
        ]
        
        # データベースに投入
        created_count = 0
        
        # 動物名を投入
        for name in animal_names:
            obj, created = AnonymousName.objects.get_or_create(
                name=name,
                defaults={'category': 'animal'}
            )
            if created:
                created_count += 1
        
        # 植物名を投入
        for name in plant_names:
            obj, created = AnonymousName.objects.get_or_create(
                name=name,
                defaults={'category': 'plant'}
            )
            if created:
                created_count += 1
        
        # 無機物名を投入
        for name in inorganic_names:
            obj, created = AnonymousName.objects.get_or_create(
                name=name,
                defaults={'category': 'inorganic'}
            )
            if created:
                created_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Created {created_count} new anonymous names')
        )
        self.stdout.write(f'Total anonymous names in database: {AnonymousName.objects.count()}')
        
        # カテゴリ別の統計
        animal_count = AnonymousName.objects.filter(category='animal').count()
        plant_count = AnonymousName.objects.filter(category='plant').count()
        inorganic_count = AnonymousName.objects.filter(category='inorganic').count()
        
        self.stdout.write(f'Animals: {animal_count}')
        self.stdout.write(f'Plants: {plant_count}')
        self.stdout.write(f'Inorganic: {inorganic_count}')