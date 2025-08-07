#!/usr/bin/env python3
"""
Script pour créer les index de base de données pour optimiser les performances
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

def create_database_indexes():
    """Crée les index de base de données pour optimiser les performances"""
    
    # Configuration de la base de données
    db_uri = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    
    try:
        # Créer la connexion
        engine = create_engine(db_uri)
        
        with engine.connect() as conn:
            print("�� Création des index de base de données...")
            
            # Index pour la table pointage
            indexes = [
                # Index simple sur user_id
                "CREATE INDEX IF NOT EXISTS idx_pointage_user_id ON pointage(user_id);",
                
                # Index simple sur date
                "CREATE INDEX IF NOT EXISTS idx_pointage_date ON pointage(date);",
                
                # Index simple sur type
                "CREATE INDEX IF NOT EXISTS idx_pointage_type ON pointage(type);",
                
                # Index simple sur retard
                "CREATE INDEX IF NOT EXISTS idx_pointage_retard ON pointage(retard);",
                
                # Index composite user_id + date
                "CREATE INDEX IF NOT EXISTS idx_pointage_user_date ON pointage(user_id, date);",
                
                # Index composite date + type
                "CREATE INDEX IF NOT EXISTS idx_pointage_date_type ON pointage(date, type);",
                
                # Index composite user_id + date + type
                "CREATE INDEX IF NOT EXISTS idx_pointage_user_date_type ON pointage(user_id, date, type);",
                
                # Index pour la table user
                "CREATE INDEX IF NOT EXISTS idx_user_role ON \"user\"(role);",
                "CREATE INDEX IF NOT EXISTS idx_user_active ON \"user\"(is_active);",
                "CREATE INDEX IF NOT EXISTS idx_user_departement ON \"user\"(departement);",
                "CREATE INDEX IF NOT EXISTS idx_user_role_active ON \"user\"(role, is_active);",
                
                # Index pour la table conge
                "CREATE INDEX IF NOT EXISTS idx_conge_user_id ON conge(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_conge_statut ON conge(statut);",
                "CREATE INDEX IF NOT EXISTS idx_conge_dates ON conge(date_debut, date_fin);",
                "CREATE INDEX IF NOT EXISTS idx_conge_user_statut ON conge(user_id, statut);",
                
                # Index pour la table login_attempt
                "CREATE INDEX IF NOT EXISTS idx_login_attempt_matricule ON login_attempt(matricule);",
                "CREATE INDEX IF NOT EXISTS idx_login_attempt_timestamp ON login_attempt(timestamp);",
                "CREATE INDEX IF NOT EXISTS idx_login_attempt_matricule_timestamp ON login_attempt(matricule, timestamp);"
            ]
            
            for index_sql in indexes:
                try:
                    conn.execute(text(index_sql))
                    print(f"✅ Index créé avec succès")
                except Exception as e:
                    print(f"⚠️  Index déjà existant ou erreur: {e}")
            
            conn.commit()
            print("�� Tous les index ont été créés avec succès!")
            
            # Afficher les statistiques des index
            print("\n📊 Statistiques des index créés:")
            result = conn.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    indexdef
                FROM pg_indexes 
                WHERE schemaname = 'public' 
                AND indexname LIKE 'idx_%'
                ORDER BY tablename, indexname;
            """))
            
            for row in result:
                print(f"  - {row.indexname} sur {row.tablename}")
            
            return True
            
    except Exception as e:
        print(f"❌ Erreur lors de la création des index: {str(e)}")
        return False

if __name__ == "__main__":
    success = create_database_indexes()
    if success:
        print("\n🚀 Les optimisations de base de données sont terminées!")
        print("💡 Redémarrez votre application pour profiter des améliorations de performance.")
    else:
        print("\n❌ Échec de la création des index.")
        sys.exit(1)