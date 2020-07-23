from flask import Flask, render_template, make_response, request
import sys
import os
import time
import uuid
from datetime import datetime
import urllib.parse as urlparse
import random
from random import randrange #Resource that helped with coding this application https://stackoverflow.com/questions/3996904/generate-random-integers-between-0-and-9

app = Flask(__name__)


serverid = uuid.uuid4()
#QR code https://www.the-qrcode-generator.com/ 
#hosted on Firebase 

roomDict = {"pool": dict(), "fitnesscenter": dict(), "lobby": dict(), "restaurant": dict()} #https://stackoverflow.com/questions/3199171/append-multiple-values-for-one-key-in-a-dictionary
roomlist = ["pool", "fitnesscenter", "lobby", "restaurant"]
prizes = ["One Free Drink"] #More prizes based on hotel requirements 
winnersdict = dict()


def format_server_time():
    server_time = time.localtime()
    return time.strftime("%I:%M:%S %p", server_time)



# If we had more time we would implement a database which would keep the user state in the cloud. 
@app.route('/')
def index():
    context = {'server_time': format_server_time()}
    action = str(request.args.get(
        'action'))  # https://stackoverflow.com/questions/24892035/how-can-i-get-the-named-parameters-from-a-url-using-flask
    print("action ", action, file=sys.stderr)
    url = "" #holds a vaild path url so we can track user via cookies a production model would use logins and authentications via that hotels loyalty program
    cookie = request.cookies.get("__session")
    #check if a valid cookie exists in user browser and append the appropriate path (error checking)
    print("***  ", cookie is not None and  action not in roomlist and '__session' in request.cookies)
    resp = make_response(render_template('index.html', context=context, actionvar=url))
    resp.headers['Cache-Control'] = 'max-age=0, no-cache, no-store, must-revalidate, proxy-revalidate, private'  # https://stackoverflow.com/questions/44929653/firebase-cloud-function-wont-store-cookie-named-other-than-session & Felix Wyss
    if cookie is not None and  action not in roomlist and '__session' in request.cookies:
        for key in roomDict:
            print("cookie ", cookie, file=sys.stderr)
            if str(cookie) in str(roomDict[key].keys()):  # we found the cookie
                action = key
                print("path is now valid ", action, file=sys.stderr)
                break
    if action is not None and action in roomlist:
        url = action
    print("url for navbar: ", url , file=sys.stderr)
    print("before index dict ", request.cookies, file=sys.stderr)
    print("cookie ", cookie, file=sys.stderr)
    print("before any changes to room dict", file=sys.stderr)
    print(roomDict, file=sys.stderr)
    resp = make_response(render_template('index.html', context=context, actionvar=url))
    resp.headers['Cache-Control'] = 'max-age=0, no-cache, no-store, must-revalidate, proxy-revalidate, private'  # https://stackoverflow.com/questions/44929653/firebase-cloud-function-wont-store-cookie-named-other-than-session
    updatedict() #removes inactive users (cookies) from roomDict 
    if action is None or action not in roomlist: #checks if the action is valid and the user actually has a cookie
        print("returned from index", file=sys.stderr)
        print(roomDict, file=sys.stderr)
        return  resp
    elif cookie is not None or '__session' in request.cookies and action is not None and action in roomlist: #https://stackoverflow.com/questions/13531149/check-for-a-cookie-with-python-flask #modifes an existing cookie
        #if a cookie exists and is not in the dictionary we need to add it provided the cookie time is still valid
        print("cookie exists", file=sys.stderr)
        if not any(
                roomDict.values()):  # https://stackoverflow.com/questions/46793033/pythonic-way-to-check-empty-dictionary-and-empty-values:

            roomDict[action][cookie] = datetime.utcnow()
            print("roomdict after adding non-existent cookie with valid action", roomDict, file=sys.stderr)
            return resp
        if cookie in roomDict[str(action)].keys():  # if the cookie exists in the dictionary we need to extend it
                roomDict[str(action)][cookie] = datetime.utcnow()
                print("cookie time extended", roomDict, file=sys.stderr)
                return resp
            # if cookie exists in room but action is different move the cookie location
        if cookie not in roomDict[str(action)].values():
            for key in roomDict:
                    #print("roomDict[key].values()", roomDict[key].keys())
                    print("cookie ", cookie, file=sys.stderr)
                    if str(cookie) in str(roomDict[key].keys()): #we found the cookie
                        del roomDict[key][cookie]
                        roomDict[str(action)][cookie] = datetime.utcnow()
                        print("changed room location ", roomDict, file=sys.stderr)
                        return resp
        if cookie not in roomDict[str(action)].keys():  # expires if cookie is not in roomDict
            print("cookie  not in local dict so deleting cookie: ", file=sys.stderr)
            resp.set_cookie('__session', cookie, expires=0)
            return resp
    else: #https://pythonise.com/series/learning-flask/flask-cookies  #makes a new cookie
        __sessionID = str(uuid.uuid4())
        print("cookieusr: ", __sessionID)
        if action is None:
            print("none", file=sys.stderr)
            print(roomDict, file=sys.stderr)
            return resp
        roomDict[action][__sessionID] = datetime.utcnow()
        resp.set_cookie("__session", __sessionID)
        print("roomdict: ", roomDict, file=sys.stderr)
        return resp



@app.route('/areadashboard.html')
def areadashboard(): #https://stackoverflow.com/questions/31965558/how-to-display-a-variable-in-html
   
    cookie = request.cookies.get("__session")
    context = { 'server_time': format_server_time() }
    updatedict()  #update the dictionary and get rid of inactive users 
    ref = request.referrer #https://stackoverflow.com/questions/28593235/get-referring-url-for-flask-request
    parsed = urlparse.urlparse(ref) #https://stackoverflow.com/questions/5074803/retrieving-parameters-from-a-url
    room = str(parsed.query).strip('action=')
    action = str(request.args.get('action')).strip()
    url = ""
    print("ref url before any checks", ref, file=sys.stderr)
    print("parsedquery ", parsed.query, file=sys.stderr)
    print("checking if room is in the roomlist", file=sys.stderr)
    print(room in roomlist, file=sys.stderr)
    print("action args ", action, file=sys.stderr)
    if room == "restaur": #fixes parsing of ant from restaurant 
        room += "ant"
    if room is not None and room in roomlist and cookie is not None:
        url = room
        roomDict[room][cookie] = datetime.utcnow() #updates user status as active
        print("updated time for user", roomDict[room][cookie], file=sys.stderr)
    elif action is not None and action in roomlist and cookie is not None:
        url = action
        roomDict[action][cookie] = datetime.utcnow()  # updates user status as active
        print("updated time for user", roomDict[action][cookie], file=sys.stderr)
    print("ref: ", ref, file=sys.stderr)
    print("room: ", room, file=sys.stderr)
    print("url: ", url, file=sys.stderr)
    resp = make_response( render_template('areadashboard.html' , context = context, actionvar =url , poolvar = len(roomDict["pool"]), fitvar = len(roomDict["fitnesscenter"]), lobbyvar =  len(roomDict["lobby"]), restvar =  len(roomDict["restaurant"])))
    resp.headers["X-Server-ID"] = str(serverid)
    resp.headers['Cache-Control'] = 'max-age=0, no-cache, no-store, must-revalidate, proxy-revalidate, private'
    if '__session' not in request.cookies:
        return resp
    return resp

@app.route('/rewards')
def rewards():
    context = {'server_time': format_server_time()}
    cookie = request.cookies.get("__session")
    num = randrange(11)
    ref = request.referrer  # https://stackoverflow.com/questions/28593235/get-referring-url-for-flask-request
    parsed = urlparse.urlparse(ref)  # https://stackoverflow.com/questions/5074803/retrieving-parameters-from-a-url
    room = str(parsed.query).strip('action=')
    action =  str(request.args.get('action')).strip()
    url = ""
    canplay = True #checks to see if the user already refreshed the page
    print("ref url before any checks", ref, file=sys.stderr)
    print("checking if room is in the roomlist", file=sys.stderr)
    print(room in roomlist, file=sys.stderr)
    print("action args ", action, file=sys.stderr)
    print("room: ", room, file=sys.stderr)
    print("cookie: ", cookie, file=sys.stderr)
    print("act: ", action, file=sys.stderr)
    if cookie is None or not any(roomDict.values()) or '__session' not in request.cookies:
        resp = make_response(render_template('emptyuser.html', context=context))
        resp.headers['Cache-Control'] = 'max-age=0, no-cache, no-store, must-revalidate, proxy-revalidate, private'
        return resp
    if room == "restaur":
        room += "ant"
    if room is not None and room in roomlist and cookie is not None:
        url = room
        currenttime = datetime.utcnow()
        elapsedtime = currenttime - roomDict[room][cookie]
        print("elapsed time: ", str(elapsedtime), file=sys.stderr)
        if elapsedtime.seconds <= 300: #300
            canplay = False
        roomDict[room][cookie] = datetime.utcnow()  # updates user status as active
        print("updated time for user", roomDict[room][cookie], file=sys.stderr)
    elif action is not None and action in roomlist and cookie is not None:
        url = action
        currenttime = datetime.utcnow()
        elapsedtime = currenttime - roomDict[action][cookie]
        print("elapsed time: ", str(elapsedtime), file=sys.stderr)
        if elapsedtime.seconds <= 300:
            canplay = False
        roomDict[action][cookie] = datetime.utcnow()  # updates user status as active
        print("updated time for user", roomDict[action][cookie], file=sys.stderr)
    print("ref: ", ref, file=sys.stderr)
    print("room: ", room, file=sys.stderr)
    print("url: ", url, file=sys.stderr)
    print("num: ", num, file=sys.stderr)
    print("cookie: ", cookie, file=sys.stderr)
    print("canplay: ", canplay, file=sys.stderr)
    if cookie in winnersdict.keys():
        resp = make_response(render_template('alreadywon.html', context=context, actionvar=url))
        resp.headers["X-Server-ID"] = str(serverid)
        resp.headers['Cache-Control'] = 'max-age=0, no-cache, no-store, must-revalidate, proxy-revalidate, private'
        return resp
    if num  <= 2 and canplay: #winner!
        prize =  random.choice(prizes)
        winnersdict[cookie] = prize
        print("prize: ", prize, file=sys.stderr)
        # if this was production this code would send an email to the hotel with the winners cookie ID and prize
        resp = make_response(render_template('winner.html',context=context, actionvar=url))
        resp.headers["X-Server-ID"] = str(serverid)
        resp.headers['Cache-Control'] = 'max-age=0, no-cache, no-store, must-revalidate, proxy-revalidate, private'
        return resp
    resp = make_response(render_template('trylater.html', context=context, actionvar=url))
    resp.headers["X-Server-ID"] = str(serverid)
    resp.headers['Cache-Control'] = 'max-age=0, no-cache, no-store, must-revalidate, proxy-revalidate, private'
    return resp




def updatedict():
    currenttime = datetime.utcnow()  # https://blog.softhints.com/python-3-subtrack-time/
    print("curr time: ", str(currenttime), file=sys.stderr)
    for key in roomDict:
        for users in list(roomDict[key]):
            elapsedtime = currenttime - roomDict[key][users]
            print("elapsed time: ", str(elapsedtime), file=sys.stderr)
            print(key, "->", roomDict[key], "users ", users, "->", roomDict[key][users], file=sys.stderr)
            if elapsedtime.seconds >= 900: #deletes user after 15 mins of inactivity
                if users in winnersdict:
                    del winnersdict[users]
                del roomDict[key][users]  # credit geekforgreeks
                print("user deleted b/c they were inactive", file=sys.stderr)
                print("roomdict after deleting", roomDict, file=sys.stderr)


@app.route('/voucher.html')
def voucher():
    context = { 'server_time': format_server_time() }
    ref = request.referrer #https://stackoverflow.com/questions/28593235/get-referring-url-for-flask-request
    parsed = urlparse.urlparse(ref) #https://stackoverflow.com/questions/5074803/retrieving-parameters-from-a-url
    room = str(parsed.query).strip('action=')
    action = str(request.args.get('action')).strip()
    url = ""
    print("ref url before any checks", ref, file=sys.stderr)
    print("parsedquery ", parsed.query, file=sys.stderr)
    print("checking if room is in the roomlist", file=sys.stderr)
    print(room in roomlist, file=sys.stderr)
    print("action args ", action, file=sys.stderr)
    if room == "restaur":
        room += "ant"
    if room is not None and room in roomlist:
        url = room
    elif action is not None and action in roomlist:
        url = action
    print("ref: ", ref, file=sys.stderr)
    print("room: ", room, file=sys.stderr)
    print("url: ", url, file=sys.stderr)
    resp = make_response( render_template('voucher.html' , context = context, actionvar =url ))
    resp.headers["X-Server-ID"] = str(serverid)
    resp.headers['Cache-Control'] = 'max-age=0, no-cache, no-store, must-revalidate, proxy-revalidate, private'
    return resp 

@app.route('/checkout.html')
def checkout(): #https://pythonbasics.org/flask-cookies/     #delete cookie see: https://stackoverflow.com/questions/14386304/flask-how-to-remove-cookies
    cookie = request.cookies.get("__session")
    print("cookie: checkout ", cookie)
    context = {'server_time': format_server_time()}
    ref = request.referrer  # https://stackoverflow.com/questions/28593235/get-referring-url-for-flask-request
    parsed = urlparse.urlparse(ref)  # https://stackoverflow.com/questions/5074803/retrieving-parameters-from-a-url
    room = str(parsed.query).strip('action=')
    action = str(request.args.get('action')).strip()
    url = ""
    print("ref url before any checks", ref, file=sys.stderr)
    print("parsedquery ", parsed.query, file=sys.stderr)
    print("checking if room is in the roomlist", file=sys.stderr)
    print(room in roomlist, file=sys.stderr)
    print("action args ", action, file=sys.stderr)
    resp = make_response(render_template('emptyuser.html', context=context))
    if room == "restaur":
        room += "ant"
    if room is not None and room in roomlist:
        url = room
    elif action is not None and action in roomlist:
        url = action
    if cookie is None or not any(roomDict):
        return resp
    resp = make_response(render_template('checkout.html', context=context, actionvar=url))
    if cookie in winnersdict.keys():
        del winnersdict[cookie]
    if room is not None and room in roomlist:
        del roomDict[room][cookie]
        resp.headers["X-Server-ID"] = str(serverid)
        resp.set_cookie('__session', cookie, expires=0)  # deletes cookie
        return resp
    elif action is not None and action in roomlist:
        del roomDict[action][cookie]
        resp.headers["X-Server-ID"] = str(serverid)
        resp.set_cookie('__session', cookie, expires=0)  # deletes cookie
        return resp
    resp = make_response(render_template('emptyuser.html', context=context))
    return resp


@app.route('/getcookie')
def getcookie():#debugging page 
    name = request.cookies.get('__session')
    print("name ", name, file=sys.stderr)
    if name is None:
        resp = make_response('<h1>Welcome ' + "failed to get cookie" + " " + str(serverid) + " " + "roomdict: " + str(roomDict)+ "winner: " + str(winnersdict) + '</h1>')
        resp.headers['Cache-Control'] = 'max-age=0, no-cache, no-store, must-revalidate, proxy-revalidate, private'
        return resp
    resp = make_response('<h1>Welcome ' + str(name) + " " + str(serverid) + " " + "roomdict: " + str(roomDict) + "winner: " + str(winnersdict) +'</h1>')
    resp.headers['Cache-Control'] = 'max-age=0, no-cache, no-store, must-revalidate, proxy-revalidate, private'
    return resp

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0',port=int(os.environ.get('PORT', 8080)))