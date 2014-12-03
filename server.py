import flask
import machineer.schemata
import json
import rq
import time
import sys
import redis


app = flask.Flask(__name__)
app.host = '0.0.0.0'
app.debug = True
r = redis.Redis()
q = rq.Queue ( connection = r, async = False )


@app.route('/api/', methods = ['POST'])
def api_post_root(): 
        return json.dumps (
              machineer.schemata.list_ ()
            , indent = 2
            )

@app.route('/api/<glob>', methods = ['POST'])
def api_post_glob(glob):

    if glob == 'test':
        return json.dumps (
                  flask.request.json
                , indent = 2
                )

    if glob != '':
        return json.dumps (
              machineer.schemata.list_ (glob)
            , indent = 2
            ) 

@app.route('/api/methods/<c>', methods = ['POST'])
def api_post_methods(c):
    return json.dumps (
              machineer.schemata.api [c] .keys()
            , indent = 2
            )


@app.route('/api/class/<c>/<f>', methods = ['POST'])
def api_post_class(c, f):

    if c == 'test':
        return json.dumps (flask.request.json)

    if f in machineer.schemata.api [c] .keys() :
        return json.dumps (
                  machineer.schemata.api [c] [f] (flask.request.json)
                , indent = 2
                )

    flask.abort(404)


if __name__ == '__main__':
    app.run(host = app.host, debug = app.debug)
