from flask import Blueprint, request, jsonify
from flask_cors import CORS

import src.connect_pg as connect_pg
import src.apiException as apiException

from src.config import config
from src.services.user_service import get_utilisateur_statement

import psycopg2
from psycopg2 import errorcodes

from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity  
user = Blueprint('user', __name__)


@user.route('/utilisateurs/get', methods=['GET','POST'])
@jwt_required()
def get_utilisateur():
    """Renvoit tous les utilisateurs via la route /utilisateurs/get
    
    :return:  tous les utilisateurs
    :rtype: json
    """
    query = "select * from utilisateur order by IdUtilisateur asc"
    conn = connect_pg.connect()
    rows = connect_pg.get_query(conn, query)
    returnStatement = []
    try:
        for row in rows:
            returnStatement.append(get_utilisateur_statement(row))
    except(TypeError) as e:
        return jsonify({'error': str(apiException.AucuneDonneeTrouverException("utilisateur"))}), 404
    connect_pg.disconnect(conn)
    return jsonify(returnStatement)


@user.route('/utilisateurs/get/<userName>', methods=['GET','POST'])
@jwt_required()
def get_one_utilisateur(userName):
    """Renvoit un utilisateur spécifié par son id via la route /utilisateurs/get<userName>
    
    :param IdUtilisateur: id d'un utilisateur présent dans la base de donnée
    :type IdUtilisateur: Numérique
    
    :raises DonneeIntrouvableException: Impossible de trouver l'id spécifié dans la table utilisateur
    :raises ParamètreTypeInvalideException: Le type de l’id est invalide
    
    :return:  l'utilisateur a qui appartient cette id
    :rtype: json
    """
    #query = "select * from utilisateur where IdUtilisateur=%(IdUtilisateur)s" % {'IdUtilisateur': userName}
    query = f"select * from utilisateur where Username='{userName}'"

    conn = connect_pg.connect()
    rows = connect_pg.get_query(conn, query)
    returnStatement = {}
    if (userName.isdigit() or type(userName) != str):
        return jsonify({'error': str(apiException.ParamètreTypeInvalideException("userName", "string"))}), 400
    try:
        if len(rows) > 0:
            returnStatement = get_utilisateur_statement(rows[0])
    except(TypeError) as e:
        return jsonify({'error': str(apiException.DonneeIntrouvableException("utilisateur", userName))}), 404
    connect_pg.disconnect(conn)
    return jsonify(returnStatement)


@user.route('/utilisateurs/add', methods=['POST'])
@jwt_required()
def add_utilisateur():
    """Permet d'ajouter un utilisateur via la route /utilisateurs/add
    
    :raises InsertionImpossibleException: Impossible d'ajouter l'utilisateur spécifié dans la table utilisateur
    
    :return: l'utilisateur qui vient d'être créé
    :rtype: json
    """
    json_datas = request.get_json()
    returnStatement = {}
    query = f"Insert into utilisateur (FirstName, LastName, Username, PassWord) values ('{json_datas['FirstName']}', '{json_datas['LastName']}', '{json_datas['Username']}', '{json_datas['PassWord']}') returning IdUtilisateur"
    conn = connect_pg.connect()
    try:
        returnStatement = connect_pg.execute_commands(conn, query)
    except psycopg2.IntegrityError as e:
        if e.pgcode == errorcodes.UNIQUE_VIOLATION:
            # Erreur violation de contrainte unique
            return jsonify({'error': str(apiException.DonneeExistanteException(json_datas['Username'], "Username", "utilisateur"))}), 400
        else:
            # Erreur inconnue
            return jsonify({'error': str(apiException.InsertionImpossibleException("utilisateur"))}), 500

    connect_pg.disconnect(conn)
    return jsonify(returnStatement)

@user.route('/utilisateurs/auth', methods=['GET'])
def auth_utilisateur():
    """ Permet d'authentifier un utilisateur via la route /utilisateurs/auth

    :raises DonneeIntrouvableException: Impossible de trouver l'Username spécifié dans la table utilisateur
    :raises ParamètreTypeInvalideException: Le type de l’Username est invalide
    
    :return: jwt token
    """
    
    json_datas = request.get_json()
    username = json_datas['Username']
    password = json_datas['PassWord']
    query = f"select PassWord, FirstLogin from utilisateur where Username='{username}'"
    conn = connect_pg.connect()
    
    rows = connect_pg.get_query(conn, query)
    
    if (username.isdigit() or type(username) != str):
        return jsonify({'error': str(apiException.ParamètreTypeInvalideException("username", "string"))}), 400
    if (not rows):
        return jsonify({'error': str(apiException.DonneeIntrouvableException("utilisateur", username))}), 404
    
    
    if (rows[0][0] == password):
       accessToken =  create_access_token(identity=username)
       return jsonify(accessToken=accessToken, firstLogin=rows[0][1])
   
    return jsonify({'error': str(apiException.LoginOuMotDePasseInvalideException())}), 400


#firstLogin route wich update the password and the firstLogin column
@user.route('/utilisateurs/firstLogin', methods=['POST'])
@jwt_required()
def firstLogin_utilisateur():
    username = get_jwt_identity()
    json_datas = request.get_json()
    password = json_datas['PassWord']
    if(password == ""):
        return jsonify({'error': str(apiException.ParamètreTypeInvalideException("password", "string"))}), 400    
    query = f"update utilisateur set PassWord='{password}', FirstLogin=false where Username='{username}'"
    conn = connect_pg.connect()
    try:
        
        connect_pg.execute_commands(conn, query)
    except:
        return jsonify({'error': str(apiException.InsertionImpossibleException("utilisateur"))}), 500
    connect_pg.disconnect(conn)
    
    
        
    
    





    

