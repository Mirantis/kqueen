#!/usr/bin/env python3
from datetime import datetime
from kqueen.models import Organization, User
from kqueen.server import create_app

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("organization", help="Organization name")
parser.add_argument("namespace", help="Organization namespace")
parser.add_argument("username", help="Admin username")
parser.add_argument("password", help="Admin password")

organization_id = '22d8df64-4ac9-4be0-89a7-c45ea0fc85da'
user_id = '09587e34-812d-4efc-af17-fbfd7315674c'


def main():
    args = parser.parse_args()
    app = create_app()
    with app.app_context():
        # Organization and user
        try:
            organization = Organization(
                id=organization_id,
                name=args.organization,
                namespace=args.namespace,
                created_at=datetime.utcnow()
            )
            organization.save()
            print('Organization {} successfully created!'.format(organization.name))
        except Exception:
            raise Exception('Adding {} organization failed'.format(args.organization))
        try:
            user = User.create(
                None,
                id=user_id,
                username=args.username,
                password=args.password,
                email='admin@kqueen.net',
                organization=organization,
                created_at=datetime.utcnow(),
                role='superadmin',
                active=True
            )
            user.save()
            print('User {} successfully created!'.format(user.username))
        except Exception:
            raise Exception('Adding {} user failed'.format(args.username))


if __name__ == "__main__":
    main()
