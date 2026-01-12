from django.core.management.base import BaseCommand
from carros.models import Marca, Modelo


class Command(BaseCommand):
    help = "Insere marcas comuns em Portugal e alguns modelos associados."

    def handle(self, *args, **options):
        data = {
            "Audi": ["A1", "A3", "A4", "A5", "A6", "Q2", "Q3", "Q5", "TT"],
            "BMW": ["116d", "118d", "120d", "320d", "330d", "X1", "X3", "X5", "i3"],
            "Mercedes-Benz": ["A 180", "A 200", "C 200", "C 220d", "E 220d", "GLA", "GLC", "CLA", "Sprinter"],
            "Volkswagen": ["Polo", "Golf", "Passat", "Tiguan", "T-Roc", "Taigo", "Touran", "Transporter"],
            "SEAT": ["Ibiza", "Leon", "Arona", "Ateca"],
            "Škoda": ["Fabia", "Scala", "Octavia", "Superb", "Kamiq", "Karoq", "Kodiaq"],
            "Renault": ["Clio", "Megane", "Captur", "Kadjar", "Austral", "Twingo", "Kangoo"],
            "Peugeot": ["208", "2008", "308", "3008", "5008", "Partner"],
            "Citroën": ["C3", "C4", "C5 Aircross", "Berlingo"],
            "Opel": ["Corsa", "Astra", "Insignia", "Mokka", "Crossland"],
            "Ford": ["Fiesta", "Focus", "Puma", "Kuga", "Transit"],
            "Toyota": ["Yaris", "Corolla", "C-HR", "RAV4", "Auris", "Hilux"],
            "Honda": ["Civic", "Jazz", "HR-V", "CR-V"],
            "Hyundai": ["i10", "i20", "i30", "Kona", "Tucson", "Santa Fe"],
            "Kia": ["Rio", "Ceed", "Stonic", "Sportage", "Niro", "Picanto"],
            "Nissan": ["Micra", "Juke", "Qashqai", "X-Trail", "Leaf"],
            "Dacia": ["Sandero", "Duster", "Jogger", "Logan"],
            "Fiat": ["500", "Panda", "Tipo", "Doblo"],
            "MINI": ["One", "Cooper", "Countryman"],
            "Volvo": ["V40", "V60", "XC40", "XC60", "XC90"],
            "Land Rover": ["Range Rover Evoque", "Discovery Sport", "Range Rover Sport"],
            "Jeep": ["Renegade", "Compass", "Wrangler"],
            "Mazda": ["Mazda2", "Mazda3", "CX-3", "CX-30", "CX-5"],
            "Suzuki": ["Swift", "Vitara", "S-Cross", "Ignis"],
            "Mitsubishi": ["ASX", "Outlander", "Eclipse Cross"],
            "Tesla": ["Model 3", "Model Y", "Model S"],
        }

        created_marcas = 0
        created_modelos = 0

        for marca_nome, modelos in data.items():
            marca, created = Marca.objects.get_or_create(nome=marca_nome)
            if created:
                created_marcas += 1

            for modelo_nome in modelos:
                _, m_created = Modelo.objects.get_or_create(marca=marca, nome=modelo_nome)
                if m_created:
                    created_modelos += 1

        self.stdout.write(self.style.SUCCESS(
            f"Seed concluído: {created_marcas} marcas criadas, {created_modelos} modelos criados."
        ))
