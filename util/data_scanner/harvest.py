import db
from datasets import maurer
import os


MODELS = [maurer.MaurerTas,
          maurer.MaurerTasmax]


def main():
    db_path = '/tmp/datasets.sqlite'
    if os.path.exists(db_path):
        os.remove(db_path)
    db.build_database(db_path=db_path)
    with db.session_scope(commit=True) as session:
        for model in MODELS:
            print('inserting model: {0}'.format(model.__class__.__name__))
            model().insert(session)


if __name__ == '__main__':
    main()
