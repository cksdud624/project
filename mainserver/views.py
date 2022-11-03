from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import scheduletable, usertable
import json
import sqlite3



updatefield = []
@csrf_exempt
def test2(request):
    if request.method == "POST":
        data = json.loads(request.body.decode('utf-8'))
        authcheck = usertable.objects.filter(userID=data['todatalist'][0]['userid'],
                                             groupID=data['todatalist'][0]['groupID'],
                                             caltype=data['todatalist'][0]['caltype'])
        queryset = authcheck.values_list()
        authquery = queryset[0][5]
        if data['todatalist'][0]['commandtype'] == "exportcalendar":
            if authquery == "2" or authquery == "3":
                for i in range(0, len(data['todatalist'])):
                    schedulesearch = scheduletable.objects.filter(caltype=data['todatalist'][i]['caltype'],
                                                              groupID=data['todatalist'][i]['groupID'],
                                                              year=data['todatalist'][i]['year'],
                                                              month=data['todatalist'][i]['month'],
                                                              day=data['todatalist'][i]['day'],
                                                              hour=data['todatalist'][i]['hour'],
                                                              minute=data['todatalist'][i]['minute'],
                                                              content=data['todatalist'][i]['content'],)
                    if schedulesearch.count() == 0:
                        scheduleinsert = scheduletable(userID=data['todatalist'][i]['userid'], caltype=data['todatalist'][i]['caltype'],
                                                       groupID=data['todatalist'][i]['groupID'],
                                                       year=data['todatalist'][i]['year'],
                                                       month=data['todatalist'][i]['month'], day=data['todatalist'][i]['day'],
                                                       hour=data['todatalist'][i]['hour'], minute=data['todatalist'][i]['minute'],
                                                       content=data['todatalist'][i]['content'])
                        scheduleinsert.save()
                return HttpResponse("export complete")
            else:
                return HttpResponse("Authrity error")



@csrf_exempt
def test(request):
    if request.method == "POST":
        data = json.loads(request.body.decode('utf-8'))
        #일정 생성
        if data['commandtype'] == "insertschedule":
            authcheck = usertable.objects.filter(userID=data['userid'], groupID=data['groupID'], caltype=data['caltype'])
            scheduleinsert = scheduletable(userID=data['userid'], caltype=data['caltype'], groupID=data['groupID'],
                                        year=data['year'],
                                           month=data['month'], day=data['day'],
                                           hour=data['hour'], minute=data['minute'],
                                           content=data['content'])
            #일정 리스트화
            queryset = authcheck.values_list()
            authquery = queryset[0][5]
            if authquery == "2" or authquery == "3":
                scheduleinsert.save()
                return HttpResponse("insert complete")
            else:
                return HttpResponse("Authority error")
        #사용자ID 생성
        elif data['commandtype'] == "createid":
            #사용자ID 조회
            useridcheck = usertable.objects.filter(userID=data['userid'])
            if useridcheck.count() == 0:
                createid = usertable(userID=data['userid'], caltype="Public", password=data['password'], groupID=1,
                                     authrank="2")
                createid.save()
                return HttpResponse("ID created")
            else:
                return HttpResponse("ID already exists")
        #사용자ID 변경
        elif data['commandtype'] == "changeid":
            #사용자ID 및 패스워드 조회
            useridcheck = usertable.objects.filter(userID=data['userid'], password=data['password'])
            if useridcheck.count() == 0:
                return HttpResponse("ID not exists or Password error")
            else:
                return HttpResponse("ID exists")
        #사용자ID 삭제
        elif data['commandtype'] == "deleteid":
            #사용자ID 조회
            useridcheck = usertable.objects.filter(userID=data['userid'])
            #패스워드 검사
            passwordcheck = usertable.objects.filter(userID=data['userid'], password=data['password'], caltype="Public")
            #사용자의 퍼블릭 캘린더 일정 삭제
            deletealldate = scheduletable.objects.filter(userID=data['userid'], caltype="Public")
            #사용자의 권한 유일성 검사
            checkgroupid = usertable.objects.filter(userID=data['userid'], caltype='Group')
            queryset = checkgroupid.values_list()
            if useridcheck.count() >= 1:
                if passwordcheck.count() >= 1:
                    for i in range(0, len(queryset)):
                        checkauth = usertable.objects.filter(userID=data['userid'], caltype='Group',
                                                             groupID=queryset[i],
                                                             authrank="3")
                        if checkauth.count() >= 1:
                            return HttpResponse("delete groupID first")
                    #남아있는 그룹 캘린더 일정 교체
                    connectdb = sqlite3.connect('db.sqlite3')
                    conn = connectdb.cursor()
                    conn.execute('UPDATE mainserver_scheduletable SET userID = 0 WHERE caltype = :group AND'
                                 ' userID = :userID', {"group": 'Group', "userID": data['userid']})
                    connectdb.commit()
                    useridcheck.delete()
                    deletealldate.delete()
                    return HttpResponse("ID deleted")
                else:
                    return HttpResponse("Password error")
            else:
                return HttpResponse("ID not exists")
        #캘린더ID생성
        elif data['commandtype'] == "groupIDcreate":
            #캘린더ID 조회
            groupidcheck = usertable.objects.filter(groupID=data['groupID'])
            if groupidcheck.count() == 0:
                groupIDcreate = usertable(userID=data['userid'], caltype="Group", grouppassword=data['password'],
                                          groupID=data['groupID'], authrank="3")
                groupIDcreate.save()
                return HttpResponse("GroupID created")
            else:
                return HttpResponse("GroupID already exists")
        #캘린더ID변경
        elif data['commandtype'] == "groupIDchange":
            #캘린더ID 및 패스워드 조회
            groupidcheck = usertable.objects.filter(groupID=data['groupID'], caltype="Group",
                                                    grouppassword=data['password'])
            #사용자의 캘린더 등록 여부
            usergroupidcheck = usertable.objects.filter(groupID=data['groupID'], caltype="Group", userID=data['userid'])
            if groupidcheck.count() == 0:
                return HttpResponse("ID not exists or Password error")
            else:
                if usergroupidcheck.count() == 0:
                    #사용자가 캘린더에 등록되어 있지 않으면 등록
                    groupIDcreate = usertable(userID=data['userid'], caltype="Group",
                                              groupID=data['groupID'], authrank="1")
                    groupIDcreate.save()
                return HttpResponse("GroupID exists")
        #캘린더ID삭제
        elif data['commandtype'] == "groupIDdelete":
            #캘린더 조회
            groupidcheck = usertable.objects.filter(groupID=data['groupID'], caltype="Group")
            #캘린더 권한 조회
            groupauthcheck = usertable.objects.filter(groupID=data['groupID'], caltype="Group",
                                                      userID=data['userid'], authrank="3")
            #캘린더 패스워드 조회
            grouppasswordcheck = usertable.objects.filter(groupID=data['groupID'], caltype="Group",
                                                          grouppassword=data['password'])
            #삭제된 캘린더의 일정 삭제
            groupscheduledelete = scheduletable.objects.filter(groupID=data['groupID'], caltype="Group")
            if groupidcheck.count() == 0:
                return HttpResponse("GroupID not exists")
            else:
                if groupauthcheck.count() == 0:
                    return HttpResponse("Authority error")
                else:
                    if grouppasswordcheck.count() == 0:
                        return HttpResponse("GroupPassword error")
                    else:
                        groupscheduledelete.delete()
                        groupidcheck.delete()
                        return HttpResponse("GroupID deleted")
        #그룹 캘린더 관리 화면 사용자 조회
        elif data['commandtype'] == "searchcurrentgroup":
            #그룹 캘린더 사용자 조회
            groupidcheck = usertable.objects.filter(userID=data['userid'], groupID=data['groupID'], caltype="Group")
            #사용자 권환 조회
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
                    #사용자들의 정보를 JSON파일로 응답
                    for i in conn.fetchall():
                        jsonfile.append({
                                "userid": i[0],
                                "authrank": i[1]
                        })
                        jsonparse = json.dumps({'items': jsonfile})
                    return HttpResponse(jsonparse)
        #그룹 캘린더 관리 화면 권한 변경
        elif data['commandtype'] == "changeauthrank":
            #그룹 캘린더 사용자 조회
            useridcheck = usertable.objects.filter(userID=data['userid'], groupID=data['groupID'], caltype="Group")
            #사용자 권한 조회
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
                #권한 변경
                if auth3users.count() == 0:
                    sql = 'UPDATE mainserver_usertable SET authrank = :authrank WHERE userID = :userid AND' \
                          ' groupID = :groupID AND caltype = :group'
                    sqldata = ('3', data['userid'], data['groupID'], 'Group')
                    conn.execute(sql, sqldata)
                    connectdb.commit()
                    return HttpResponse("auth 3 user not exists")
                else:
                    return HttpResponse("authrank change complete")
        #사용자ID, 권한 조회
        elif data['commandtype'] == "searchcalendardata":
            #캘린더ID 조회
            groupidcheck = usertable.objects.filter(groupID=data['groupID'])
            #사용자 권한 조회
            userauthcheck = usertable.objects.filter(groupID=data['groupID'], userID=data['useridforcheck'], authrank="3")
            if groupidcheck.count() == 0:
                return HttpResponse("ID not exists")
            else:
                if(userauthcheck.count() == 0):
                    return HttpResponse("Authority error")
                else:
                    #사용자ID, 권한 조회
                    useridcheck = usertable.objects.filter(userID__contains=data['userid'], groupID=data['groupID'], caltype="Group"
                                                       ,authrank__contains=data['authrank'])
                    queryset = useridcheck.values_list()
                    jsonfile = []
                    #사용자ID, 권한 JSON파일로 응답
                    for i in range(useridcheck.count()):
                        jsonfile.append({
                            "userid": queryset[i][1],
                            "authrank": queryset[i][5]
                        })
                    jsonparse = json.dumps({'items': jsonfile})
                    return HttpResponse(jsonparse)
        #일정 삭제
        elif data['commandtype'] == "deleteschedule":
            #사용자 권한 조회
            userauthcheck = usertable.objects.filter(groupID=data['groupID'], userID=data['userid'])
            #삭제할 일정 조회
            scheduledelete = scheduletable.objects.get(userID=data['userid'], caltype=data['caltype'], groupID=data['groupID'],
                                           year=data['year'],
                                           month=data['month'], day=data['day'],
                                           hour=data['hour'], minute=data['minute'],
                                           content=data['content'])
            #일정 리스트화
            queryset = userauthcheck.values_list()
            authquery = queryset[0][5]
            if authquery == "2" or authquery == "3":
                scheduledelete.delete()
                return HttpResponse("delete complete")
            else:
                return HttpResponse("Authority error")
        #일정 변경
        elif data['commandtype'] == "updateschedule":
            #변경 전 일정 검색
            userauthcheck = usertable.objects.filter(groupID=data['groupID'], userID=data['userid'])
            queryset = userauthcheck.values_list()
            authquery = queryset[0][5]
            if authquery == "2" or authquery == "3":
                updatefield.append(data['hour'])
                updatefield.append(data['minute'])
                updatefield.append(data['content'])
                return HttpResponse("update ready")
            else:
                return HttpResponse("Authority error")
        elif data['commandtype'] == "updateschedule2":
            #변경 전 일정
            currentdatacheck = scheduletable.objects.filter(userID=data['userid'], caltype=data['caltype'],
                                                    groupID=data['groupID'],
                                                    year=data['year'], month=data['month'], day=data['day'],
                                                    hour=updatefield[0], minute=updatefield[1], content=updatefield[2])
            if currentdatacheck.count() == 1:
                #일정 변경
                currentdata = scheduletable.objects.get(userID=data['userid'], caltype=data['caltype'],
                                                        groupID=data['groupID'],
                                                        year=data['year'], month=data['month'], day=data['day'],
                                                        hour=updatefield[0], minute=updatefield[1],
                                                        content=updatefield[2])
                currentdata.hour = data['hour']
                currentdata.minute = data['minute']
                currentdata.content = data['content']
                currentdata.save()
                updatefield.clear()
                return HttpResponse("update complete")
            updatefield.clear()
            return HttpResponse("no schedule")
        #캘린더 불러오기
        elif data['commandtype'] == "importcalendar":
            #사용자 권한 조회
            userauthcheck = usertable.objects.filter(groupID=data['groupID'], userID=data['userid'])
            #그룹 캘린더 모든 일정 조회
            calendardata = scheduletable.objects.filter(groupID=data['groupID'], caltype=data['caltype'])
            queryset = userauthcheck.values_list()
            calendarqueryset = calendardata.values_list()
            jsonfile = []
            authquery = queryset[0][5]
            if authquery == "2" or authquery == "3":
            #그룹 캘린더 JSON파일 응답
                for i in range(calendardata.count()):
                    jsonfile.append({
                        "year": calendarqueryset[i][4],
                        "month": calendarqueryset[i][5],
                        "day": calendarqueryset[i][6],
                        "hour": calendarqueryset[i][7],
                        "minute": calendarqueryset[i][8],
                        "content": calendarqueryset[i][9],
                    })
                jsonparse = json.dumps({'todatalist': jsonfile})
                return HttpResponse(jsonparse)
            else:
                return HttpResponse("Authority error")
        else:
            return HttpResponse(data[0]['commandtype'])
