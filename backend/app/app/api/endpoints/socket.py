import socket
from fastapi import APIRouter, Depends, Form,File,UploadFile
from app.models import *
from app.core.security import *
from app.utils import *
from app.api import deps
from sqlalchemy.orm import Session
from sqlalchemy import extract
from datetime import datetime,date
from typing import List
from app.core import config
import openai
import json
from pydub import AudioSegment

router = APIRouter() 




@router.post("/sockets") 
async def sockets(text:str=Form(None)):

    # Create a socket object
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = socket.gethostname()
    
    # Define the server's IP address and port
    server_address = ('192.168.1.185', 8001)

    # Connect to the server
    sock.connect(server_address)
    print("Connected to", server_address)

    # try:
    # Send data to the server
    sock.sendall(text.encode())

    # Receive data from the server
    data = sock.recv(1024)
    print("Received:", data.decode())
    # finally:
    #     # Close the socket
    #     sock.close()
     
    
@router.post("/sockets_send") 
async def sockets_send(text:str=Form(None)):

    # Create a socket object
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = socket.gethostname()
    
    # Define the server's IP address and port
    server_address = ('192.168.1.185', 8002)

    # Connect to the server
    sock.connect(server_address)
    print("Connected to", server_address)

    # try:
    # Send data to the server
    sock.sendall(text.encode())

    # Receive data from the server
    data = sock.recv(1024)
    print("Received:", data.decode())
    # finally:
    #     # Close the socket
    #     sock.close()