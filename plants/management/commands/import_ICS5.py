from django.core.management.base import BaseCommand, CommandError
from plants.models import *
from frontend.models import Actions, Transactions
from login.models import AuthUser
import csv, re

def parent_transaction(p_id):
    # find the most recent transcations associated with the plant ID, and return the transaction ID of the transaction
    last_transaction = Transactions.objects.filter(plants_id = p_id).last()
    return last_transaction.id

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('-first', nargs='?', help='Use if importing the ICS5 data in the first round of parsing. Many data in this stage were skipped because of inconsistencies.')
        #parser.add_argument('-second', nargs='?', help='Use if importing the ICS5 data in the second round of parsing. This imports most of the data skipped in the first round.')
        parser.add_argument('-all', nargs='?', help='Use if importing the ICS5 data from both first and second round of parsing.')
        
    def handle(self, *args, **options):
        path1 = r'./plants/management/csvdata/ICS5_2015.csv'
        path2 = r'./plants/management/csvdata/ICS5_2016.csv'
        path3 = r'./plants/management/csvdata/ICS5_2017.csv'

        user = AuthUser.objects.get(username='ICS5')
        
       #  if args == '-first':
#             csv_import(path1, user)
#             csv_import(path2, user)
#             csv_import(path3, user)
#         #if args == '-second':
#             #csv_import2(path1, user)
#             #csv_import2(path2, user)
#             #csv_import2(path3, user)
#         if args == '-all' or None:
#             print("in args")
        csv_import(path1, user)
        csv_import(path2, user)
        csv_import(path3, user)
            #csv_import2(path1, user)
            #csv_import2(path2, user)
            #csv_import2(path3, user)

scientific_names_list = []
transaction_list = []

properties_1_to_1 = ['common_name',
                     'drought_tol_id',
                     'flood_tol_id',
                     'humidity_tol_id',
                     'salt_tol_id',
                     'toxin_removal_id',
                     'wind_tol_id',
                     'minimum_temperature_tol',
                     'inoculant',
                     'fire_tol_id',
                     'livestock_bloat_id',
                     'pH_min',
                     'pH_max',
                     'toxicity_id',
                     'lifespan_id',
                     'allelopathic_id',
                     'tags',
                     'allelochemicals',
                     'serotiny_id',
                     'degree_of_serotiny_id',
                     'family_id',
                     'family_common_name_id']

properties_many_with_region = ['active_growth_period',
                               'animal_attractor',
                               'animal_regulator',
                               'barrier',
                               'canopy_density',
                               'duration',
                               'endemic_status',
                               'erosion_control',
                               'nutrient_requirements',
                               'harvest_period',
                               'height_at_maturity',
                               'insect_attractor',
                               'insect_regulator',
                               'leaf_retention',
                               'shade_tol',
                               'soil_drainage_tol',
                               'spread_at_maturity',
                               'sun_needs',
                               'water_needs']
                                
properties_1_to_many = ['family',
                        'family_common_name',
                        ]

properties_scientific_name = ['scientific_name']

properties_many_to_many = ['biochemical_material_prod',
                           'cultural_and_amenity_prod',
                           'flower_color',
                           'foliage_color',
                           'food_prod',
                           'animal_food',
                           'fruit_color',
                           'layer',
                           'medicinals_prod',
                           'mineral_nutrients_prod',
                           'raw_materials_prod'
                           ]

def csv_import(path, user):
    print("in import method")
    plant_name_ids = { }
    for p in Plant.objects.all():
        plant_name_ids[p.get_scientific_name] = p.id
    
    with open(path) as f:
        reader = csv.DictReader(f)
        for i,plant in enumerate(reader):
            trans_type = 'INSERT'
            actions = []

            if not(plant['Scientific Name']):
                continue
            print(i, plant['Scientific Name'], len(plant['Scientific Name']))

            scientific_name = ''
            genus = ''
            species = '' 
            variety = ''
            subspecies = ''
            cultivar = ''

            scientific_name = plant['Scientific Name']
            if 'spp.' in scientific_name:
                if scientific_name.endswith('spp.'):
                    print("spp only, delete transaction")
                    continue
                else:
                    sciname_bits= scientific_name.split()
                    found = False
                    for i in sciname_bits:
                        if "spp." in i:
                            found = True
                        if found:
                            subspecies = ' ' + i
                            continue
            if ' x ' in scientific_name:
                sciname_bits= scientific_name.split()
                genus = sciname_bits[0] + " x " + sciname_bits[2]
                species = ''
            if "'" in scientific_name:
                sciname_bits= scientific_name.split()
                for index, i in enumerate(sciname_bits):
                    if i.startswith("'") and i.endswith("'"):
                        cultivar = ' ' + i
                        if index<2 and genus is None:
                            genus = sciname_bits[0]
                            species = ''
            if 'var. ' in scientific_name:
                sciname_bits= scientific_name.split()
                found = False
                for i in sciname_bits:
                    if "Var. " or "var. " in i:
                        found = True
                    if found:
                        variety = ' ' + i
                        continue
            if genus is '':
                sciname_bits = scientific_name.split()
                genus = sciname_bits[0]
                if len(sciname_bits) > 1:
                    species = ' ' + sciname_bits[1]
                else:
                    print("genus only, delete transaction")
                    continue
            
            #check if this scientific name is already in the database
            #if scientific name has already been added, then this should be an update transaction, not an insert
            whole_db_scientific_name = genus + species + subspecies + variety + cultivar
            if whole_db_scientific_name in plant_name_ids:
                print('plant in database, update!')
                trans_type = 'UPDATE'
                p_id = plant_name_ids[whole_db_scientific_name]
                transaction = Transactions.objects.create(users_id=user.id, transaction_type=trans_type, plants_id=p_id, parent_transaction=parent_transaction(p_id), ignore=False)#because the transactions haven't been processed and Plants haven't been created, we need to keep track of which plant this is an update to. I'm saving the transaction id of the INSERT plant to the plants_id of the Update plant. In process_transactions I will use the transaction_id stored in plants_id to look it up.
            
            elif whole_db_scientific_name in scientific_names_list:
                trans_type = 'UPDATE'
                s_index =scientific_names_list.index(whole_db_scientific_name)
                print("index in scientific names list: ", s_index)
                print("transaction id of that index: ", transaction_list[s_index])
                transaction = Transactions.objects.create(users_id=user.id, transaction_type=trans_type, parent_transaction=transaction_list[s_index], ignore=False)#because the transactions haven't been processed and Plants haven't been created, we need to keep track of which plant this is an update to. I'm saving the transaction id of the INSERT plant to the parent_transactions of the Update plant. In process_transactions I will use the transaction_id stored in plants_id to look it up.
            
            else:
                transaction = Transactions.objects.create(users_id=user.id, transaction_type=trans_type, ignore=False)# not always Update
            
            scientific_names_list.append(whole_db_scientific_name)
            transaction_list.append(transaction.id)
            
            #genus_id = ScientificName.objects.filter(value='genus').first()
            actions.append(Actions(transactions=transaction, action_type=trans_type, property='scientific_name', value=genus, category="genus"))
            
            if species is not '':
                #species_id = ScientificName.objects.filter(value='species').first()
                actions.append(Actions(transactions=transaction, action_type=trans_type, property='scientific_name', value=species, category="species"))
            if variety is not '':
                #variety_id = ScientificName.objects.filter(value='variety').first()
                actions.append(Actions(transactions=transaction, action_type=trans_type, property='scientific_name', value=variety, category="variety"))    
            if subspecies is not '':
                #subspecies_id = ScientificName.objects.filter(value='subspecies').first()
                actions.append(Actions(transactions=transaction, action_type=trans_type, property='scientific_name', value=subspecies, category="subspecies"))
            if cultivar is not '':
                #cultivar_id = ScientificName.objects.filter(value='cultivar').first()
                actions.append(Actions(transactions=transaction, action_type=trans_type, property='scientific_name', value=cultivar, category="cultivar"))


            if plant['Family Name'].strip():
                actions.append(Actions(transactions=transaction, action_type=trans_type, property='family', value=plant['Family Name'].strip().lower()))

            if plant['Common Names'].strip():
                plants_list = plant['Common Names'].splitlines()
                plants = ''
                for p in plants_list:
                    if p != '':
                        plants += p.strip()
                        if p != plants_list[-1] and p.strip()[-1] != ',':
                            plants += ", "
                        elif p.strip()[-1] == ',':
                            plants += ' '
                print('pp: ', plants)
                try:
                    actions.append(Actions(transactions=transaction, action_type=trans_type, property='common_name', value=plants))
                except:
                    continue

            if plant['Endemic status to Southern California'].strip():
                endemic_status = EndemicStatus.objects.filter(value=plant['Endemic status to Southern California'].strip().lower()).first()
                if endemic_status != None:
                    actions.append(Actions(transactions=transaction, action_type=trans_type, property='endemic_status', value=endemic_status.id))

            if plant['Duration of life'].strip():
                duration_id = Duration.objects.filter(value=plant['Duration of life'].strip().lower()).first().id
                actions.append(Actions(transactions=transaction, action_type=trans_type, property='duration', value=duration_id))

            if plant['Layer'].strip():
                layer = plant['Layer'].split(',')
                for l in layer:
                    l_id = Layer.objects.filter(value=l.strip().lower()).first().id
                    actions.append(Actions(transactions=transaction, action_type=trans_type, property='layer', value=l_id))

            if plant['Maximum canopy density'].strip():
                canopy_density_id = CanopyDensity.objects.filter(value=plant['Maximum canopy density'].strip().lower()).first().id
                actions.append(Actions(transactions=transaction, action_type=trans_type, property='canopy_density', value=canopy_density_id))

            if plant['Leaf retention'].strip():
                leaf_retention_id = LeafRetention.objects.filter(value=plant['Leaf retention'].strip().lower()).first().id
                actions.append(Actions(transactions=transaction, action_type=trans_type, property='leaf_retention', value=leaf_retention_id))

            if plant['Primary flower color'].strip():
                flower_color = plant['Primary flower color'].split(',')
                for fc in flower_color:
                    fc_id = FlowerColor.objects.filter(value=fc.strip().lower()).first().id
                    actions.append(Actions(transactions=transaction, action_type=trans_type, property='flower_color', value=fc_id))

            if plant['Foliage color'].strip():
                foliage_color = plant['Foliage color'].split(',')
                for fc in foliage_color:
                    fc_id = FoliageColor.objects.filter(value=fc.strip().lower()).first().id
                    actions.append(Actions(transactions=transaction, action_type=trans_type, property='foliage_color', value=fc_id))

            if plant['Fruit color (when ripe)'].strip():
                fruit_color = plant['Fruit color (when ripe)'].split(',')
                for fc in fruit_color:
                    fc_id = FruitColor.objects.filter(value=fc.strip().lower()).first().id
                    actions.append(Actions(transactions=transaction, action_type=trans_type, property='fruit_color', value=fc_id))
            
            if plant['Degree of serotiny'].strip():
                degree_of_serotiny = plant['Degree of serotiny'].strip().lower()
                if 'strongly serotinous' in degree_of_serotiny:
                    degree_of_serotiny_id = DegreeOfSerotiny.objects.filter(value='strongly serotinous').first().id
                    actions.append(Actions(transactions=transaction, action_type=trans_type, property='degree_of_serotiny_id', value=degree_of_serotiny_id))
                elif 'weakly serotinous' in degree_of_serotiny:
                    degree_of_serotiny_id = DegreeOfSerotiny.objects.filter(value='weakly serotinous').first().id
                    actions.append(Actions(transactions=transaction, action_type=trans_type, property='degree_of_serotiny_id', value=degree_of_serotiny_id))
                elif 'facultatively serotinous' in degree_of_serotiny:
                    degree_of_serotiny_id = DegreeOfSerotiny.objects.filter(value='facultatively serotinous').first().id
                    actions.append(Actions(transactions=transaction, action_type=trans_type, property='degree_of_serotiny_id', value=degree_of_serotiny_id))
                elif 'non-serotinous' in degree_of_serotiny:
                    degree_of_serotiny_id = DegreeOfSerotiny.objects.filter(value='non-serotinous').first().id
                    actions.append(Actions(transactions=transaction, action_type=trans_type, property='degree_of_serotiny_id', value=degree_of_serotiny_id))

            if plant['Shade tolerance'].strip():
                shade_tol = plant['Shade tolerance'].split(',')
                for st in shade_tol:
                    st_id = ShadeTol.objects.filter(value=st.strip().lower()).first().id
                    actions.append(Actions(transactions=transaction, action_type=trans_type, property='shade_tol', value=st_id))

            if plant['Salt tolerance'].strip():
                salt_tol = plant['Salt tolerance'].strip().lower()
                if 'moderately salt-tolerant' in salt_tol:
                    salt_told_id = SaltTol.objects.filter(value='moderately salt-tolerant').first().id
                    actions.append(Actions(transactions=transaction, action_type=trans_type, property='salt_tol_id', value=salt_told_id))
                elif 'slightly salt-tolerant' in salt_tol:
                    salt_told_id = SaltTol.objects.filter(value='slightly salt-tolerant').first().id
                    actions.append(Actions(transactions=transaction, action_type=trans_type, property='salt_tol_id', value=salt_told_id))
                elif 'not salt-tolerant' in salt_tol:
                    salt_told_id = SaltTol.objects.filter(value='not salt-tolerant').first().id
                    actions.append(Actions(transactions=transaction, action_type=trans_type, property='salt_tol_id', value=salt_told_id))
                elif 'salt-tolerant' in salt_tol:
                    salt_told_id = SaltTol.objects.filter(value='salt-tolerant').first().id
                    actions.append(Actions(transactions=transaction, action_type=trans_type, property='salt_tol_id', value=salt_told_id))
    
            if plant['Flood tolerance'].strip():
                flood_tol = plant['Flood tolerance'].strip().lower()
                if 'moderately flood-tolerant' in flood_tol:
                    flood_tol_id = FloodTol.objects.filter(value='moderately flood-tolerant').first().id
                    actions.append(Actions(transactions=transaction, action_type=trans_type, property='flood_tol_id', value=flood_tol_id))
                elif 'not flood-tolerant' in flood_tol:
                    flood_tol_id = FloodTol.objects.filter(value='not flood-tolerant').first().id
                    actions.append(Actions(transactions=transaction, action_type=trans_type, property='flood_tol_id', value=flood_tol_id))
                elif 'flood-tolerant' in flood_tol:
                    flood_tol_id = FloodTol.objects.filter(value='flood-tolerant').first().id
                    actions.append(Actions(transactions=transaction, action_type=trans_type, property='flood_tol_id', value=flood_tol_id))

            if plant['Drought tolerance'].strip():
                drought_tol = plant['Drought tolerance'].strip().lower()
                if 'moderately drought-tolerant' in drought_tol:
                    drought_tol_id = DroughtTol.objects.filter(value='moderately drought-tolerant').first().id
                    actions.append(Actions(transactions=transaction, action_type=trans_type, property='drought_tol_id', value=drought_tol_id))
                elif 'not drought-tolerant' in drought_tol:
                    drought_tol_id = DroughtTol.objects.filter(value='not drought-tolerant').first().id
                    actions.append(Actions(transactions=transaction, action_type=trans_type, property='drought_tol_id', value=drought_tol_id))
                elif 'drought-tolerant' in drought_tol:
                    drought_tol_id = DroughtTol.objects.filter(value='drought-tolerant').first().id
                    actions.append(Actions(transactions=transaction, action_type=trans_type, property='drought_tol_id', value=drought_tol_id))

            if plant['Humidity tolerance'].strip():
                humidity_tol = plant['Humidity tolerance'].strip().lower()
                if 'moderately humidity-tolerant' in humidity_tol:
                    humidity_tol_id = HumidityTol.objects.filter(value='moderately humidity-tolerant').first().id
                    actions.append(Actions(transactions=transaction, action_type=trans_type, property='humidity_tol_id', value=humidity_tol_id))
                elif 'not humidity-tolerant' in humidity_tol:
                    humidity_tol_id = HumidityTol.objects.filter(value='not humidity-tolerant').first().id
                    actions.append(Actions(transactions=transaction, action_type=trans_type, property='humidity_tol_id', value=humidity_tol_id))
                elif 'humidity-tolerant' in humidity_tol:
                    humidity_tol_id = HumidityTol.objects.filter(value='humidity-tolerant').first().id
                    actions.append(Actions(transactions=transaction, action_type=trans_type, property='humidity_tol_id', value=humidity_tol_id))
            
            if plant['Fire tolerance'].strip():
                fire_tol = plant['Fire tolerance'].strip().lower()
                if 'resistant to fire' in fire_tol:
                    fire_tol_id = FireTol.objects.filter(value='resistant to fire').first().id
                    actions.append(Actions(transactions=transaction, action_type=trans_type, property='fire_tol_id', value=fire_tol_id))
                elif 'not resistant to fire' in fire_tol:
                    fire_tol_id = FireTol.objects.filter(value='not resistant to fire').first().id
                    actions.append(Actions(transactions=transaction, action_type=trans_type, property='fire_tol_id', value=fire_tol_id))
                elif 'accelerates fire' in fire_tol:
                    fire_tol_id = FireTol.objects.filter(value='accelerates fire').first().id
                    actions.append(Actions(transactions=transaction, action_type=trans_type, property='fire_tol_id', value=fire_tol_id))
                
            if plant['Nutrient requirements'].strip():
                nutrient_req = NutrientRequirements.objects.filter(value=plant['Nutrient requirements'].strip().lower()).first()
                if nutrient_req != None:
                    actions.append(Actions(transactions=transaction, action_type=trans_type, property='nutrient_requirements', value=nutrient_req.id))
            
            if plant['Sun light requirements'].strip():
                sun_light = plant['Sun light requirements'].split(',')
                for sl in sun_light:
                    sl_id = SunNeeds.objects.filter(value=sl.strip().lower()).first().id
                    actions.append(Actions(transactions=transaction, action_type=trans_type, property='sun_needs', value=sl_id))

            if plant['Serotiny'].strip():
                serotiny = plant['Serotiny'].strip().lower()
                if 'none' in serotiny:
                    serotiny_id = Serotiny.objects.filter(value='none').first().id
                    actions.append(Actions(transactions=transaction, action_type=trans_type, property='serotiny_id', value=serotiny_id))
                elif 'necriscene' in serotiny:
                    serotiny_id = Serotiny.objects.filter(value='necriscene').first().id
                    actions.append(Actions(transactions=transaction, action_type=trans_type, property='serotiny_id', value=serotiny_id))
                elif 'hygriscene' in serotiny:
                    serotiny_id = Serotiny.objects.filter(value='hygriscene').first().id
                    actions.append(Actions(transactions=transaction, action_type=trans_type, property='serotiny_id', value=serotiny_id))
                elif 'soliscene' in serotiny:
                    serotiny_id = Serotiny.objects.filter(value='soliscene').first().id
                    actions.append(Actions(transactions=transaction, action_type=trans_type, property='serotiny_id', value=serotiny_id))
                elif 'xeriscene' in serotiny:
                    serotiny_id = Serotiny.objects.filter(value='xeriscene').first().id
                    actions.append(Actions(transactions=transaction, action_type=trans_type, property='serotiny_id', value=serotiny_id))
                elif 'pyriscene' in serotiny:
                    serotiny_id = Serotiny.objects.filter(value='pyriscene').first().id
                    actions.append(Actions(transactions=transaction, action_type=trans_type, property='serotiny_id', value=serotiny_id))
                elif 'phyrohydriscene' in serotiny:
                    serotiny_id = Serotiny.objects.filter(value='phyrohydriscene').first().id
                    actions.append(Actions(transactions=transaction, action_type=trans_type, property='serotiny_id', value=serotiny_id))

            if plant['Raw materials'].strip():
                raw_materials = plant['Raw materials'].split(',')
                for rm in raw_materials:
                    raw_mat = RawMaterialsProd.objects.filter(value=rm.strip().lower()).first()
                    if raw_mat != None:
                        actions.append(Actions(transactions=transaction, action_type=trans_type, property='raw_materials_prod', value=raw_mat.id))

            if plant['Medicinal'].strip():
                medicinal = plant['Medicinal'].split(',')
                for m in medicinal:
                    med = MedicinalsProd.objects.filter(value=m.strip().lower()).first()
                    if med != None:
                        actions.append(Actions(transactions=transaction, action_type=trans_type, property='medicinals_prod', value=med.id))
            
            if plant['Biochemical material'].strip():
                biochem_material = plant['Biochemical material'].split(',')
                for bm in biochem_material:
                    biochem = BiochemicalMaterialProd.objects.filter(value=bm.strip().lower()).first()
                    if biochem != None:
                        actions.append(Actions(transactions=transaction, action_type=trans_type, property='biochemical_material_prod', value=biochem.id))
            
            if plant['Cultural and amenity'].strip():
                cultural_amenity = plant['Cultural and amenity'].split(',')
                for ca in cultural_amenity:
                    cultural = CulturalAndAmenityProd.objects.filter(value=ca.strip().lower()).first()
                    if cultural != None:
                        actions.append(Actions(transactions=transaction, action_type=trans_type, property='cultural_and_amenity_prod', value=cultural.id))
            
            if plant['Nutrients added to soil'].strip():
                nutrients_added = plant['Nutrients added to soil'].split(',')
                for n in nutrients_added:
                    nutrient = MineralNutrientsProd.objects.filter(value=n.strip().lower()).first()
                    if nutrient != None:
                        actions.append(Actions(transactions=transaction, action_type=trans_type, property='mineral_nutrients_prod', value=nutrient.id))
            
            if plant['Erosion Control'].strip():
                erosion_control_id = ErosionControl.objects.filter(value=plant['Erosion Control'].strip().lower()).first().id
                actions.append(Actions(transactions=transaction, action_type=trans_type, property='erosion_control', value=erosion_control_id))
            
            if plant['Toxicity to human and livestock'].strip():
                toxicity_id = Toxicity.objects.filter(value=plant['Toxicity to human and livestock'].strip().lower()).first().id
                actions.append(Actions(transactions=transaction, action_type=trans_type, property='toxicity_id', value=toxicity_id))

            if plant['pH range'].strip():
                pH_range = re.split('- | to', plant['pH range'].strip())
                try:
                    if len(pH_range) == 2:
                        actions.append(Actions(transactions=transaction, action_type=trans_type, property='pH_min', value=float(pH_range[0].strip())))
                        actions.append(Actions(transactions=transaction, action_type=trans_type, property='pH_max', value=float(pH_range[1].strip())))
                except:
                    print("data doesn't meet parsable standard")
                    
            if plant['Wind tolerance'].strip():
                wind_tol = plant['Wind tolerance'].strip().lower()
                if 'very' in wind_tol:
                    wind_tol_id = WindTol.objects.filter(value='very wind tolerant').first().id
                    actions.append(Actions(transactions=transaction, action_type=trans_type, property='wind_tol_id', value=wind_tol_id))
                elif 'moderately' in wind_tol:
                    wind_tol_id = WindTol.objects.filter(value='moderately wind tolerant').first().id
                    actions.append(Actions(transactions=transaction, action_type=trans_type, property='wind_tol_id', value=wind_tol_id))
                elif 'somewhat' in wind_tol:
                    wind_tol_id = WindTol.objects.filter(value='somewhat wind-tolerant').first().id
                    actions.append(Actions(transactions=transaction, action_type=trans_type, property='wind_tol_id', value=wind_tol_id))
                elif 'not' in wind_tol:
                    wind_tol_id = WindTol.objects.filter(value='not wind-tolerant').first().id
                    actions.append(Actions(transactions=transaction, action_type=trans_type, property='wind_tol_id', value=wind_tol_id))
            
            if plant['Active growth period'].strip():
                active_growth_period = plant['Active growth period'].split(',')
                for agp in active_growth_period:
                    agp_id = ActiveGrowthPeriod.objects.filter(value=agp.strip().lower()).first().id
                    actions.append(Actions(transactions=transaction, action_type=trans_type, property='active_growth_period', value=agp_id))

            if plant['Harvest period'].strip():
                harvest_period = plant['Harvest period'].split(',')
                for hp in harvest_period:
                    hp_id = HarvestPeriod.objects.filter(value=hp.strip().lower()).first().id
                    actions.append(Actions(transactions=transaction, action_type=trans_type, property='harvest_period', value=hp_id))

            if plant['Soil drainage tolerance'].strip():
                soil_drain_tol = plant['Soil drainage tolerance'].strip().lower()
                if 'poor-drainage tolerant' in soil_drain_tol:
                    soil_drain_tol_id = SoilDrainageTol.objects.filter(value='poor-drainage tolerant').first().id
                    actions.append(Actions(transactions=transaction, action_type=trans_type, property='soil_drainage_tol', value=soil_drain_tol_id))
                elif 'somewhat-poor-drainage tolerant' in soil_drain_tol:
                    soil_drain_tol_id = SoilDrainageTol.objects.filter(value='somewhat-poor-drainage tolerant').first().id
                    actions.append(Actions(transactions=transaction, action_type=trans_type, property='soil_drainage_tol', value=soil_drain_tol_id))
                elif 'moderate-drainage tolerant' in soil_drain_tol:
                    soil_drain_tol_id = SoilDrainageTol.objects.filter(value='moderate-drainage tolerant').first().id
                    actions.append(Actions(transactions=transaction, action_type=trans_type, property='soil_drainage_tol', value=soil_drain_tol_id))
                elif 'well-drained tolerant' in soil_drain_tol:
                    soil_drain_tol_id = SoilDrainageTol.objects.filter(value='well-drained tolerant').first().id
                    actions.append(Actions(transactions=transaction, action_type=trans_type, property='soil_drainage_tol', value=soil_drain_tol_id))
                elif 'excessively-drained tolerant' in soil_drain_tol:
                    soil_drain_tol_id = SoilDrainageTol.objects.filter(value='excessively-drained tolerant').first().id
                    actions.append(Actions(transactions=transaction, action_type=trans_type, property='soil_drainage_tol', value=soil_drain_tol_id))
                    
            if plant['Innoculant'].strip():
                actions.append(Actions(transactions=transaction, action_type=trans_type, property='inoculant', value=plant['Innoculant'].strip().lower()))

            if plant['Human food'].strip():
                human_food = plant['Human food'].strip()
                if "greens" in human_food:
                    hf_id = FoodProd.objects.filter(value='greens').first().id
                    actions.append(Actions(transactions=transaction, action_type=trans_type, property='food_prod', value=hf_id))
                if "grains" in human_food:
                    hf_id = FoodProd.objects.filter(value='grains').first().id
                    actions.append(Actions(transactions=transaction, action_type=trans_type, property='food_prod', value=hf_id))
                if "vegetables" in human_food:
                    hf_id = FoodProd.objects.filter(value='vegetables').first().id
                    actions.append(Actions(transactions=transaction, action_type=trans_type, property='food_prod', value=hf_id))
                if "nuts" in human_food:
                    hf_id = FoodProd.objects.filter(value='nuts').first().id
                    actions.append(Actions(transactions=transaction, action_type=trans_type, property='food_prod', value=hf_id))
                if "fruit" in human_food:
                    hf_id = FoodProd.objects.filter(value='fruit').first().id
                    actions.append(Actions(transactions=transaction, action_type=trans_type, property='food_prod', value=hf_id))

            if plant['Allelochemicals'].strip():
                allelo = plant['Allelochemicals'].strip().lower()
                if allelo == 'no' or allelo == 'none':
                    allelo_id = Allelopathic.objects.filter(value='no').first().id
                    actions.append(Actions(transactions=transaction, action_type=trans_type, property='allelopathic_id', value=allelo_id))
                elif allelo == 'yes':
                    allelo_id = Allelopathic.objects.filter(value='yes').first().id
                    actions.append(Actions(transactions=transaction, action_type=trans_type, property='allelopathic_id', value=allelo_id))
            
            Actions.objects.bulk_create(actions)



# def csv_import2(path, user):
#   plant_name_ids = { }
#   for p in Plant.objects.all():
#       plant_name_ids[p.get_scientific_name] = p.id
# 
#   with open(path) as f:
#       reader = csv.DictReader(f)
#       for i,plant in enumerate(reader):
#           trans_type = 'INSERT'
#           actions = []
# 
#           if not(plant['Scientific Name']):
#               continue
#           print(i, plant['Scientific Name'], len(plant['Scientific Name']))
# 
#           scientific_name = ''
#           genus = ''
#           species = '' 
#           variety = ''
#           subspecies = ''
#           cultivar = ''
# 
#           scientific_name = plant['Scientific Name']
#           if 'spp.' in scientific_name:
#               if scientific_name.endswith('spp.'):
#                   print("spp only, delete transaction")
#                   continue
#               else:
#                   sciname_bits= scientific_name.split()
#                   found = False
#                   for i in sciname_bits:
#                       if "spp." in i:
#                           found = True
#                       if found:
#                           subspecies = ' ' + i
#                           continue
#           if ' x ' in scientific_name:
#               sciname_bits= scientific_name.split()
#               genus = sciname_bits[0] + " x " + sciname_bits[2]
#               species = ''
#           if "'" in scientific_name:
#               sciname_bits= scientific_name.split()
#               for i in sciname_bits:
#                   if i.startswith("'") and i.endswith("'"):
#                       cultivar = ' ' + i
#                       if i<2 and genus is None:
#                           genus = sciname_bits[0]
#                           species = ''
#           if 'var. ' in scientific_name:
#               sciname_bits= scientific_name.split()
#               found = False
#               for i in sciname_bits:
#                   if "Var. " or "var. " in i:
#                       found = True
#                   if found:
#                       variety = ' ' + i
#                       continue
#           if genus is '':
#               sciname_bits = scientific_name.split()
#               genus = sciname_bits[0]
#               if len(sciname_bits) > 1:
#                   species = ' ' + sciname_bits[1]
#               else:
#                   print("genus only, delete transaction")
#                   continue
#           
#           #check if this scientific name is already in the database
#           #if scientific name has already been added, then this should be an update transaction, not an insert
#           whole_db_scientific_name = genus + species + subspecies + variety + cultivar
#           if whole_db_scientific_name in plant_name_ids:
#               print('plant in database, update!')
#               trans_type = 'UPDATE'
#               p_id = plant_name_ids[whole_db_scientific_name]
#               transaction = Transactions.objects.create(users_id=user.id, transaction_type=trans_type, plants_id=p_id, parent_transaction=parent_transaction(p_id), ignore=False)#because the transactions haven't been processed and Plants haven't been created, we need to keep track of which plant this is an update to. I'm saving the transaction id of the INSERT plant to the plants_id of the Update plant. In process_transactions I will use the transaction_id stored in plants_id to look it up.
#           
#           elif whole_db_scientific_name in scientific_names_list:
#               trans_type = 'UPDATE'
#               s_index =scientific_names_list.index(whole_db_scientific_name)
#               print("index in scientific names list: ", s_index)
#               print("transaction id of that index: ", transaction_list[s_index])
#               transaction = Transactions.objects.create(users_id=user.id, transaction_type=trans_type, parent_transaction=transaction_list[s_index], ignore=False)#because the transactions haven't been processed and Plants haven't been created, we need to keep track of which plant this is an update to. I'm saving the transaction id of the INSERT plant to the parent_transactions of the Update plant. In process_transactions I will use the transaction_id stored in plants_id to look it up.
#           
#           else:
#               transaction = Transactions.objects.create(users_id=user.id, transaction_type=trans_type, ignore=False)# not always Update
#           
#           scientific_names_list.append(whole_db_scientific_name)
#           transaction_list.append(transaction.id)
#           
#           #genus_id = ScientificName.objects.filter(value='genus').first()
#           actions.append(Actions(transactions=transaction, action_type=trans_type, property='scientific_name', value=genus, category="genus"))
#           
#           if species is not '':
#               #species_id = ScientificName.objects.filter(value='species').first()
#               actions.append(Actions(transactions=transaction, action_type=trans_type, property='scientific_name', value=species, category="species"))
#           if variety is not '':
#               #variety_id = ScientificName.objects.filter(value='variety').first()
#               actions.append(Actions(transactions=transaction, action_type=trans_type, property='scientific_name', value=variety, category="variety"))    
#           if subspecies is not '':
#               #subspecies_id = ScientificName.objects.filter(value='subspecies').first()
#               actions.append(Actions(transactions=transaction, action_type=trans_type, property='scientific_name', value=subspecies, category="subspecies"))
#           if cultivar is not '':
#               #cultivar_id = ScientificName.objects.filter(value='cultivar').first()
#               actions.append(Actions(transactions=transaction, action_type=trans_type, property='scientific_name', value=cultivar, category="cultivar"))
# 
# 
# 
#           Actions.objects.bulk_create(actions)