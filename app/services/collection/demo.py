from app.services.collection.base import BaseJobConnector

class DemoConnector(BaseJobConnector):
    name = "demo"

    async def search_jobs(self, criteria: dict) -> list[dict]:
        return [
            {
                "title": "Alternant Développeur Full Stack",
                "company": "Entreprise Démo",
                "location": "Dijon",
                "contract_type": "Alternance",
                "duration_months": 36,
                "description": "Développement d'applications web avec React, TypeScript, Python et SQL.",
                "skills": ["React", "TypeScript", "Python", "SQL"],
                "source": "demo",
                "source_url": "https://example.com/jobs/demo-fullstack"
            }
        ]
