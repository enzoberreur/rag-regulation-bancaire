"""
Script pour générer des faux PDFs réglementaires pour tester l'application RAG.
"""
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import os

def create_pdf(filename, title, content_sections):
    """Créer un PDF avec le titre et les sections de contenu."""
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Style pour le titre
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor='#0066FF',
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    # Style pour les sous-titres
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor='#333333',
        spaceAfter=12,
        spaceBefore=20,
        alignment=TA_LEFT
    )
    
    # Style pour le texte
    text_style = ParagraphStyle(
        'CustomText',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_JUSTIFY,
        spaceAfter=12,
        leading=14
    )
    
    # Ajouter le titre
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Ajouter les sections
    for section_title, section_content in content_sections:
        story.append(Paragraph(section_title, heading_style))
        story.append(Paragraph(section_content, text_style))
        story.append(Spacer(1, 0.2*inch))
    
    # Générer le PDF
    doc.build(story)
    print(f"✅ PDF créé : {filename}")

# Créer le dossier data
os.makedirs("data", exist_ok=True)

# PDF 1: Régulation ACPR sur les exigences de capital climatique
create_pdf(
    "data/ACPR_Regulation_2024-15_Climate_Capital.pdf",
    "ACPR Regulation 2024-15: Climate-Related Capital Requirements",
    [
        ("Article 12: Climate Capital Requirements", 
         "Les établissements bancaires sont tenus d'appliquer des exigences de capital renforcées pour les expositions liées au climat. "
         "Les risques climatiques doivent être quantifiés et intégrés dans les modèles de calcul du capital réglementaire. "
         "Les établissements doivent établir une méthodologie de quantification des expositions climatiques conforme aux standards ACPR."),
        
        ("Article 12(3): Reporting Mensuel", 
         "Les établissements doivent soumettre un rapport mensuel à l'ACPR détaillant leurs expositions climatiques, "
         "les méthodologies utilisées, et les impacts sur les exigences de capital. Ce rapport doit être transmis "
         "avant le 5 de chaque mois pour le mois précédent."),
        
        ("Article 15: Gouvernance", 
         "Chaque établissement doit mettre en place un Comité des Risques Climatiques au niveau du conseil d'administration. "
         "Ce comité doit être composé d'au moins trois membres indépendants et doit se réunir trimestriellement. "
         "Le comité est responsable de la validation des politiques de gestion des risques climatiques."),
        
        ("Article 18: Capital Buffer", 
         "Les établissements présentant des expositions climatiques élevées doivent maintenir un coussin de capital "
         "supplémentaire de 2,5% du capital réglementaire. Ce coussin est calculé sur la base des expositions "
         "classées comme étant à haut risque climatique selon la classification ACPR."),
        
        ("Article 22: Conformité et Pénalités", 
         "La non-conformité aux dispositions de la présente régulation peut entraîner des sanctions pouvant aller "
         "jusqu'à 5% du chiffre d'affaires annuel. Les établissements ont jusqu'au 31 décembre 2025 pour se mettre "
         "en conformité avec l'ensemble des dispositions.")
    ]
)

# PDF 2: Politique interne HexaBank sur la gestion des risques
create_pdf(
    "data/HexaBank_RMP-2024-03_Risk_Management_Policy.pdf",
    "HexaBank Risk Management Policy RMP-2024-03",
    [
        ("Section 4.2: Climate Risk Framework", 
         "La présente politique définit le cadre de gestion des risques climatiques pour HexaBank. "
         "L'établissement reconnaît l'importance croissante des risques climatiques dans l'évaluation globale du risque. "
         "Une approche qualitative est privilégiée pour l'identification et l'évaluation initiale des risques climatiques."),
        
        ("Section 4.2.1: Identification des Risques", 
         "Les risques climatiques sont identifiés à travers une analyse qualitative des secteurs d'activité et des géographies. "
         "Les équipes de risques doivent documenter les risques identifiés dans un registre dédié mis à jour semestriellement."),
        
        ("Section 4.2.2: Évaluation Qualitative", 
         "L'évaluation des risques climatiques se fait selon une échelle qualitative : faible, modéré, élevé. "
         "Cette évaluation est basée sur l'expertise des analystes risques et les données sectorielles disponibles."),
        
        ("Section 4.2.3: Reporting", 
         "Un rapport trimestriel sur les risques climatiques est présenté au Comité des Risques. "
         "Ce rapport inclut une synthèse des risques identifiés et des mesures de mitigation proposées."),
        
        ("Section 4.2.4: Limitations Actuelles", 
         "La présente politique reconnaît que l'évaluation quantitative des risques climatiques n'est pas encore implémentée. "
         "Un plan de développement de capacités quantitatives est en cours d'élaboration pour une mise en œuvre prévue en 2026.")
    ]
)

# PDF 3: Guidelines ECB sur l'IA et la conformité
create_pdf(
    "data/ECB_Guidelines_2024-08_AI_Compliance.pdf",
    "ECB Guidelines 2024-08: Artificial Intelligence in Banking Operations",
    [
        ("Principle 1: Transparency and Explainability", 
         "Les établissements bancaires utilisant des systèmes d'intelligence artificielle doivent garantir la transparence "
         "et l'explicabilité des décisions automatisées. Les modèles d'IA doivent être documentés et leurs décisions "
         "doivent être traçables. Les clients doivent être informés de l'utilisation de l'IA dans les processus les concernant."),
        
        ("Principle 2: Data Quality and Governance", 
         "Les données utilisées pour entraîner et opérer les systèmes d'IA doivent être de haute qualité, "
         "représentatives et non biaisées. Un cadre de gouvernance des données doit être établi, incluant "
         "des procédures de validation et de contrôle qualité régulières."),
        
        ("Principle 3: Human Oversight", 
         "Tous les systèmes d'IA critiques doivent être soumis à une supervision humaine appropriée. "
         "Les décisions automatisées ayant un impact significatif doivent pouvoir être révisées et surchargées par des humains. "
         "Un mécanisme d'escalade doit être en place pour les cas exceptionnels."),
        
        ("Principle 4: Risk Management", 
         "Les établissements doivent intégrer les risques liés à l'IA dans leur cadre de gestion des risques existant. "
         "Une évaluation des risques spécifique à l'IA doit être réalisée avant le déploiement et régulièrement mise à jour. "
         "Les scénarios de défaillance doivent être documentés et testés."),
        
        ("Principle 5: Compliance Monitoring", 
         "Un système de monitoring continu de la conformité des systèmes d'IA doit être mis en place. "
         "Les indicateurs de performance et de conformité doivent être suivis et rapportés au management et aux autorités de supervision.")
    ]
)

# PDF 4: EU AI Act - Exigences pour le secteur bancaire
create_pdf(
    "data/EU_AI_Act_2024_Banking_Requirements.pdf",
    "EU AI Act 2024: Banking Sector Requirements",
    [
        ("Article 6: High-Risk AI Systems in Banking", 
         "Les systèmes d'IA utilisés dans le secteur bancaire pour l'évaluation du crédit, la détection de fraude, "
         "ou la gestion des risques sont classés comme systèmes à haut risque. Ces systèmes doivent respecter des exigences "
         "strictes en matière de documentation, de gouvernance et de conformité avant leur mise sur le marché."),
        
        ("Article 9: Quality Management System", 
         "Les établissements bancaires utilisant des systèmes d'IA à haut risque doivent mettre en place un système "
         "de management de la qualité conforme aux standards ISO. Ce système doit inclure des procédures de validation, "
         "de test et de monitoring des systèmes d'IA."),
        
        ("Article 13: Transparency and Information", 
         "Les utilisateurs de systèmes d'IA doivent être informés de manière claire et compréhensible lorsqu'ils interagissent "
         "avec un système d'IA. Les établissements doivent fournir des informations sur les capacités et limitations du système, "
         "ainsi que sur les droits des utilisateurs."),
        
        ("Article 15: Human Oversight", 
         "Des mesures techniques et organisationnelles doivent être mises en place pour garantir une supervision humaine "
         "appropriée des systèmes d'IA à haut risque. Cette supervision doit permettre de détecter, prévenir et corriger "
         "les dysfonctionnements ou impacts négatifs."),
        
        ("Article 72: Conformity Assessment", 
         "Les établissements doivent mener une évaluation de conformité avant la mise sur le marché ou la mise en service "
         "des systèmes d'IA à haut risque. Cette évaluation doit démontrer que le système respecte toutes les exigences "
         "pertinentes de la présente régulation. Un certificat de conformité doit être obtenu et maintenu à jour.")
    ]
)

# PDF 5: Politique interne HexaBank sur la conformité AI
create_pdf(
    "data/HexaBank_AI_Compliance_Policy_2024.pdf",
    "HexaBank AI Compliance Policy 2024",
    [
        ("Section 1: Scope and Objectives", 
         "Cette politique définit les exigences de conformité pour l'utilisation de l'intelligence artificielle dans "
         "les opérations bancaires d'HexaBank. Elle s'applique à tous les systèmes d'IA utilisés dans l'établissement, "
         "y compris ceux développés en interne et ceux acquis auprès de tiers."),
        
        ("Section 2: Governance Structure", 
         "Le Comité de Conformité IA est responsable de l'approbation de tous les nouveaux systèmes d'IA. "
         "Ce comité se réunit mensuellement et inclut des représentants des départements Risques, Conformité, IT et Business. "
         "Tous les projets d'IA doivent être soumis à ce comité avant le déploiement."),
        
        ("Section 3: Documentation Requirements", 
         "Chaque système d'IA doit être documenté selon un template standard incluant : description du système, "
         "données utilisées, algorithmes employés, procédures de test, mesures de monitoring, et procédures de gestion des incidents. "
         "Cette documentation doit être maintenue à jour et accessible aux auditeurs."),
        
        ("Section 4: Testing and Validation", 
         "Tous les systèmes d'IA doivent subir des tests rigoureux avant leur déploiement en production. "
         "Ces tests incluent des tests fonctionnels, des tests de performance, des tests de biais, et des tests de sécurité. "
         "Un rapport de test doit être validé par le Comité de Conformité IA."),
        
        ("Section 5: Ongoing Monitoring", 
         "Les systèmes d'IA en production doivent être monitorés en continu pour détecter toute dérive, "
         "baisse de performance, ou comportement anormal. Des alertes doivent être configurées et un rapport mensuel "
         "de monitoring doit être présenté au Comité de Conformité IA."),
        
        ("Section 6: Incident Management", 
         "Tout incident lié à un système d'IA doit être documenté et rapporté selon les procédures d'incident management. "
         "Les incidents critiques doivent être rapportés aux autorités de supervision dans les délais réglementaires. "
         "Un plan de réponse aux incidents doit être maintenu pour chaque système d'IA critique.")
    ]
)

print("\n🎉 Tous les PDFs de test ont été créés dans le dossier 'data/'")
print("\nFichiers créés :")
print("  - ACPR_Regulation_2024-15_Climate_Capital.pdf (Regulation)")
print("  - HexaBank_RMP-2024-03_Risk_Management_Policy.pdf (Policy)")
print("  - ECB_Guidelines_2024-08_AI_Compliance.pdf (Regulation)")
print("  - EU_AI_Act_2024_Banking_Requirements.pdf (Regulation)")
print("  - HexaBank_AI_Compliance_Policy_2024.pdf (Policy)")

