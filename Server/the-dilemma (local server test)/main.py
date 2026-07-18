from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import threading


app = Flask(__name__)
CORS(app)


lock = threading.Lock()


MAX_ROUNDS = 3


game = {

    "players": [],

    "round": 1,

    "started": False,

    "finished": False,


    "choices": {},

    "confirmed": {},


    "score": {

        "player1": 0,
        "player2": 0

    }

}





@app.route("/")
def index():

    return send_file("index.html")





@app.route("/join", methods=["POST"])
def join():

    with lock:


        if len(game["players"]) >= 2:

            return jsonify({

                "status": "WAIT PLS",
                "message": "ROOM IS FULL"

            }), 403



        player = f"player{len(game['players'])+1}"

        game["players"].append(player)



        if len(game["players"]) == 2:

            game["started"] = True



        return jsonify({

            "player": player,

            "started": game["started"]

        })







@app.route("/state")
def state():

    with lock:


        return jsonify({

            "players":
                len(game["players"]),


            "started":
                game["started"],


            "finished":
                game["finished"],


            "round":
                game["round"],


            "score":
                game["score"],


            "status":

                "GAME READY"

                if game["started"]

                else

                "WAITING FOR OPPONENT"


        })









@app.route("/select", methods=["POST"])
def select():


    data = request.json


    player = data.get("player")

    choice = data.get("choice")



    if player not in ["player1","player2"]:

        return jsonify({

            "status":"INVALID PLAYER"

        })



    if choice not in ["red","blue"]:

        return jsonify({

            "status":"INVALID CHOICE"

        })



    with lock:


        if game["finished"]:

            return jsonify({

                "status":"GAME FINISHED"

            })



        game["choices"][player] = choice



        return jsonify({

            "status":"CHOICE SAVED"

        })










def calculate():


    p1 = game["choices"]["player1"]

    p2 = game["choices"]["player2"]



    if p1 == "blue" and p2 == "blue":

        game["score"]["player1"] += 1

        game["score"]["player2"] += 1



    elif p1 == "red" and p2 == "blue":

        game["score"]["player1"] += 3



    elif p1 == "blue" and p2 == "red":

        game["score"]["player2"] += 3



    # red + red = 0







@app.route("/confirm", methods=["POST"])
def confirm():


    data=request.json


    player=data.get("player")



    with lock:


        game["confirmed"][player]=True



        if (

            game["confirmed"].get("player1")

            and

            game["confirmed"].get("player2")

        ):


            calculate()



            game["choices"].clear()

            game["confirmed"].clear()



            game["round"] += 1



            if game["round"] > MAX_ROUNDS:

                game["finished"] = True




            return jsonify({

                "status":"ROUND COMPLETE",

                "round":game["round"]

            })




        else:


            return jsonify({

                "status":"WAITING OTHER PLAYER"

            })









@app.route("/result")
def result():

    with lock:


        return jsonify({

            "finished":
                game["finished"],


            "score":
                game["score"],


            "round":
                game["round"]

        })




if __name__=="__main__":


    print("""
=============================

Truth or Dare
 └ Episode 01: THE DILEMMA 

 PORT : 8080
 MODE : LAN

=============================
""")


    app.run(

        host="0.0.0.0",

        port=8080

    )
