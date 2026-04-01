# Guide d'import du fichier JSON

## Fichier à utiliser
Le fichier JSON à importer est :

`demo_sna_notes_fixture.json`

## Où le placer
Place le fichier dans le dossier `fixtures` de ton application `scrum`.

Chemin conseillé :
```text
django_project/scrum/fixtures/demo_sna_notes_fixture.json
```

Si le dossier `fixtures` n'existe pas encore, crée-le.

## Commandes d'import
Ouvre un terminal dans le dossier où se trouve `manage.py`, puis lance :

```bash
cd django_project
python manage.py migrate
python manage.py loaddata demo_sna_notes_fixture
```

## Important
Le fichier est pensé pour une **base de démonstration**.

Le plus propre est d'importer le JSON dans une base vide ou une base de test.
S'il y a déjà des données dans la base, certains identifiants ou noms d'utilisateurs peuvent entrer en conflit.

## Repartir d'une base vide
Si tu veux une démo propre, tu peux vider la base avant l'import.

```bash
python manage.py flush --noinput
python manage.py migrate
python manage.py loaddata demo_sna_notes_fixture
```

## Comptes créés
Mot de passe pour tous :
```text
Demo1234!
```

Utilisateurs :
```text
admin
po
sm
dev
test
viewer
```

## Ce qui sera importé
Après l'import, tu auras :
- le projet **SNA - Suivi des Notes Académiques**
- 3 sprints
- des tickets de backlog
- des tickets dans le sprint actif
- des commentaires
- des activités

## Pour avoir un vrai admin global dans le projet
Selon ton projet, `admin` sera bien le créateur du projet, mais le rôle global du profil peut rester sur `member`.

Si tu veux le passer en admin global dans ton interface, lance cette commande :

```bash
python manage.py shell -c "from django.contrib.auth.models import User; u=User.objects.get(username='admin'); u.profile.global_role='admin'; u.profile.save(); print('admin configuré comme admin global')"
```

## Remarque utile
Je n'ai pas ajouté dans le JSON :
- les `Profile`
- le `Board`
- les `Column`

car ton projet les crée automatiquement via les signaux Django.

## Vérification rapide après import
Après import :
1. connecte-toi avec `admin`
2. ouvre le projet **SNA**
3. va sur le sprint actif
4. vérifie qu'il y a bien des tickets dans **To Do**, **In Progress** et **Done**
5. ouvre ensuite le rapport du projet pour voir le graphique
