#!/usr/bin/env python3

"""Opens the AWS Console authenticating you with your access key instead of
user name and password.

Based on
https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_enable-console-custom-url.html
"""
import argparse
import json
import urllib
import urllib.parse
import webbrowser

import boto3
import botocore
import requests

SESSION_DURATION = 60 * 60 * 12


def get_arguments(profile_names):
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        "-p",
        "--profile",
        choices=profile_names,
        required=True,
        help="Profile name to get role arn to assume from",
    )
    return parser.parse_args()


def get_credentials(role_arn, mfa_serial):
    sts_client = boto3.client("sts")

    try:
        assumed_role_object = sts_client.assume_role(
            RoleArn=role_arn,
            RoleSessionName="AssumeRoleSession",
        )
    except botocore.exceptions.ClientError as exception:
        error_code = exception.response["Error"]["Code"]
        if error_code != "AccessDenied" or not mfa_serial:
            raise

        mfa_token = input(f"Enter MFA code for {mfa_serial}: ")
        assumed_role_object = sts_client.assume_role(
            RoleArn=role_arn,
            RoleSessionName="AssumeRoleSession",
            SerialNumber=mfa_serial,
            TokenCode=mfa_token,
        )

    return assumed_role_object["Credentials"]


def get_signin_token(credentials):
    session_string = json.dumps(
        {
            "sessionId": credentials["AccessKeyId"],
            "sessionKey": credentials["SecretAccessKey"],
            "sessionToken": credentials["SessionToken"],
        }
    )

    query_string = urllib.parse.urlencode(
        {
            "Action": "getSigninToken",
            "Session": session_string,
            "SessionDuration": SESSION_DURATION,
        }
    )

    request_url = "https://signin.aws.amazon.com/federation?" + query_string
    response = requests.get(request_url)
    signin_token = response.json()["SigninToken"]

    return signin_token


def get_signin_url(signin_token):
    query_string = urllib.parse.urlencode(
        {
            "Action": "login",
            "Destination": "https://console.aws.amazon.com/",
            "SigninToken": signin_token,
        }
    )

    return "https://signin.aws.amazon.com/federation?" + query_string


def main():
    profiles = botocore.session.Session().full_config["profiles"]
    arguments = get_arguments(set(profiles.keys()) - {"default"})

    profile = profiles[arguments.profile]
    role_arn = profile["role_arn"]
    mfa_serial = profile.get("mfa_serial", None)

    credentials = get_credentials(role_arn, mfa_serial)
    signin_token = get_signin_token(credentials)
    signin_url = get_signin_url(signin_token)
    webbrowser.open(signin_url)


if __name__ == "__main__":
    main()
