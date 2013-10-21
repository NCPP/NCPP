import db
from datasets import maurer,hayhoe
import os
from NCPP.util.data_scanner.datasets import packages


MODELS = [maurer.MaurerTas,
          maurer.MaurerTasmax,
          maurer.MaurerTasmin,
          maurer.MaurerPrecip,
          hayhoe.HayhoeGFDLPr,
          hayhoe.HayhoeGFDLTasmax,
          hayhoe.HayhoeGFDLTasmin]

PACKAGES = [packages.HayhoeGFDLPackage,
            packages.MaurerPackage]


def main():
    db_path = '/tmp/datasets.sqlite'
    if os.path.exists(db_path):
        os.remove(db_path)
    db.build_database(db_path=db_path)
    with db.session_scope(commit=True) as session:
        for model in MODELS:
            m = model()
            print('inserting model: {0}'.format(m.__class__.__name__))
            m.insert(session)
            
        for package in PACKAGES:
            p = package()
            print('inserting package: {0}'.format(p.__class__.__name__))
            p.insert(session)


if __name__ == '__main__':
    main()
    print('success.')