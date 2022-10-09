from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import scheduletable, usertable
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from collections import OrderedDict
import google.oauth2.credentials
import google_auth_oauthlib.flow
import json
import os.path
import requests
import sqlite3
import os
from subprocess import run

SCOPES = ["https://www.googleapis.com/auth/calendar"]

service_account_email = "djangotest@djangoproject-362411.iam.gserviceaccount.com"
credentials = service_account.Credentials.from_service_account_file('keycode.json')
scoped_credentials = credentials.with_scopes(SCOPES)


@csrf_exempt
def tokentest(request):
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            output = run("echo", capture_output=True).stdout
            return HttpResponse(output)
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            output = run("echo", capture_output=True).stdout
            return HttpResponse(output)
            creds = flow.run_local_server()
        with open('token.json', 'w') as token:
            token.write(creds.to_json())


@csrf_exempt
def ex():
    service = build('calendar', 'v3', credentials=creds)
    event = {
        'summary': 'test1',
        'start': {
            'dateTime': '2022-09-27T09:00:00+09:00',
        },
        'end': {
            'dateTime': '2022-09-27T10:00:00+09:00',
        },
    }
    event = service.events().insert(calendarId='cksdud624@gmail.com', body=event).execute()

@csrf_exempt
def test(request):
    if request.method == "POST":
        data = json.loads(request.body.decode('utf-8'))
        if data['commandtype'] == "insertschedule":
            authcheck = usertable.objects.filter(userID=data['userid'], groupID=data['groupID'], caltype=data['caltype'])
            scheduleinsert = scheduletable(userID=data['userid'], caltype=data['caltype'], groupID=data['groupID'],
                                        year=data['year'],
                                           month=data['month'], day=data['day'],
                                           hour=data['hour'], minute=data['minute'],
                                           content=data['content'])
            queryset = authcheck.values_list()
            authquery = queryset[0][5]
            if authquery == "2" or authquery == "3":
                scheduleinsert.save()
                return HttpResponse("insert complete")
            else:
                return HttpResponse("Authority error")
        elif data['commandtype'] == "createid":
            useridcheck = usertable.objects.filter(userID=data['userid'])
            if useridcheck.count() == 0:
                createid = usertable(userID=data['userid'], caltype="Public", password=data['password'], groupID=1,
                                     authrank="2")
                createid.save()
                return HttpResponse("ID created")
            else:
                return HttpResponse("ID already exists")
        elif data['commandtype'] == "changeid":
            useridcheck = usertable.objects.filter(userID=data['userid'], password=data['password'])
            if useridcheck.count() == 0:
                return HttpResponse("ID not exists or Password error")
            else:
                return HttpResponse("ID exists")
        elif data['commandtype'] == "deleteid":
            useridcheck = usertable.objects.filter(userID=data['userid'])
            passwordcheck = usertable.objects.filter(userID=data['userid'], password=data['password'], caltype="Public")
            if useridcheck.count() >= 1:
                if passwordcheck.count() >= 1:
                    useridcheck.delete()
                    return HttpResponse("ID deleted")
                else:
                    return HttpResponse("Password error")
            else:
                return HttpResponse("ID not exists")
        elif data['commandtype'] == "groupIDcreate":
            groupidcheck = usertable.objects.filter(groupID=data['groupID'])
            if groupidcheck.count() == 0:
                groupIDcreate = usertable(userID=data['userid'], caltype="Group", grouppassword=data['password'],
                                          groupID=data['groupID'], authrank="3")
                groupIDcreate.save()
                return HttpResponse("GroupID created")
            else:
                return HttpResponse("GroupID already exists")
        elif data['commandtype'] == "groupIDchange":
            groupidcheck = usertable.objects.filter(groupID=data['groupID'], caltype="Group",
                                                    grouppassword=data['password'])
            usergroupidcheck = usertable.objects.filter(groupID=data['groupID'], caltype="Group", userID=data['userid'])
            if groupidcheck.count() == 0:
                return HttpResponse("ID not exists or Password error")
            else:
                if usergroupidcheck.count() == 0:
                    groupIDcreate = usertable(userID=data['userid'], caltype="Group",
                                              groupID=data['groupID'], authrank="1")
                    groupIDcreate.save()
                return HttpResponse("GroupID exists")

        elif data['commandtype'] == "groupIDdelete":
            groupidcheck = usertable.objects.filter(groupID=data['groupID'], caltype="Group")
            groupauthcheck = usertable.objects.filter(groupID=data['groupID'], caltype="Group",
                                                      userID=data['userid'], authrank="3")
            grouppasswordcheck = usertable.objects.filter(groupID=data['groupID'], caltype="Group",
                                                          grouppassword=data['password'])
            if groupidcheck.count() == 0:
                return HttpResponse("GroupID not exists")
            else:
                if groupauthcheck.count() == 0:
                    return HttpResponse("Authority error")
                else:
                    if grouppasswordcheck.count() == 0:
                        return HttpResponse("GroupPassword error")
                    else:
                        groupidcheck.delete()
                        return HttpResponse("GroupID deleted")
        elif data['commandtype'] == "searchcurrentgroup":
            groupidcheck = usertable.objects.filter(userID=data['userid'], groupID=data['groupID'], caltype="Group")
            groupauthcheck = usertable.objects.filter(groupID=data['groupID'], caltype="Group",
                                                      userID=data['userid'], authrank="3")
            if groupidcheck.count() == 0:
                return HttpResponse("GroupID not exists")
            else:
                if groupauthcheck.count() == 0:
                    return HttpResponse("Authority error")
                else:
                    connectdb = sqlite3.connect('db.sqlite3')
                    conn = connectdb.cursor()
                    conn.execute('SELECT userID, authrank from mainserver_usertable WHERE caltype = :group AND '
                                 'groupID = :groupID', {"group": 'Group', "groupID": data['groupID']})
                    jsonfile = []
                    for i in conn.fetchall():
                        jsonfile.append({
                                "userid": i[0],
                                "authrank": i[1]
                        })
                        jsonparse = json.dumps({'items': jsonfile})
                    return HttpResponse(jsonparse)
        elif data['commandtype'] == "changeauthrank":
            useridcheck = usertable.objects.filter(userID=data['userid'], groupID=data['groupID'], caltype="Group")
            auth3users = usertable.objects.filter(groupID=data['groupID'], authrank="3", caltype="Group")
            if useridcheck.count() == 0:
                return HttpResponse("ID not exists")
            else:
                connectdb = sqlite3.connect('db.sqlite3')
                conn = connectdb.cursor()
                sql = 'UPDATE mainserver_usertable SET authrank = :authrank WHERE userID = :userid AND' \
                      ' groupID = :groupID AND caltype = :group'
                sqldata = (data['authrank'], data['userid'], data['groupID'], 'Group')
                conn.execute(sql, sqldata)
                connectdb.commit()
                if auth3users.count() == 0:
                    sql = 'UPDATE mainserver_usertable SET authrank = :authrank WHERE userID = :userid AND' \
                          ' groupID = :groupID AND caltype = :group'
                    sqldata = ('3', data['userid'], data['groupID'], 'Group')
                    conn.execute(sql, sqldata)
                    connectdb.commit()
                    return HttpResponse("auth 3 user not exists")
                else:
                    return HttpResponse("authrank change complete")
        elif data['commandtype'] == "searchcalendardata":
            groupidcheck = usertable.objects.filter(groupID=data['groupID'])
            userauthcheck = usertable.objects.filter(groupID=data['groupID'], userID=data['useridforcheck'], authrank="3")
            if groupidcheck.count() == 0:
                return HttpResponse("ID not exists")
            else:
                if(userauthcheck.count() == 0):
                    return HttpResponse("Authority error")
                else:
                    useridcheck = usertable.objects.filter(userID__contains=data['userid'], groupID=data['groupID'], caltype="Group"
                                                       ,authrank__contains=data['authrank'])
                    queryset = useridcheck.values_list()
                    jsonfile = []
                    for i in range(useridcheck.count()):
                        jsonfile.append({
                            "userid": queryset[i][1],
                            "authrank": queryset[i][5]
                        })
                    jsonparse = json.dumps({'items': jsonfile})
                    return HttpResponse(jsonparse)
        else:
            return HttpResponse("test")
