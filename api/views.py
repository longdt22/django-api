from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
from .serializers import UserSerializer, PostSerializer
from .models import User, Post
from rest_framework import status
from rest_framework.authentication import get_authorization_header
from .authentication import decode_access_token
import jwt, datetime


# Create your views here.
class RegisterView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class LoginView(APIView):
    def post(self, request):
        email = request.data['email']
        password = request.data['password']

        user = User.objects.filter(email=email).first()

        if user is None:
            raise AuthenticationFailed('User not found!')

        if not user.check_password(password):
            raise AuthenticationFailed('Incorrect password!')

        payload = {
            'id': user.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60),
            'iat': datetime.datetime.utcnow()
        }

        token = jwt.encode(payload, 'secret', algorithm='HS256').decode('utf-8')

        response = Response()

        response.set_cookie(key='jwt', value=token, httponly=True)
        response.data = {
            'jwt': token
        }
        return response


class UserView(APIView):

    def get(self, request):
        token = request.COOKIES.get('jwt')

        if not token:
            raise AuthenticationFailed('Unauthenticated!')

        try:
            payload = jwt.decode(token, 'secret', algorithm=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Unauthenticated!')

        user = User.objects.filter(id=payload['id']).first()
        serializer = UserSerializer(user)
        return Response(serializer.data)


class LogoutView(APIView):
    def post(self, request):
        response = Response()
        response.delete_cookie('jwt')
        response.data = {
            'message': 'success'
        }
        return response
        
class PostView(APIView):
    # permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        posts = Post.objects.all()
        serializer = PostSerializer(posts, many = True)
        listpost = []
        for i in range(len(serializer.data)):
            print(i)
            new = serializer.data[i].copy()
            for key, value in serializer.data[i].items():
                if(key == 'user'):
                    user = User.objects.filter(id=value).first()
                    new['name'] = user.name          
            listpost.append(new) 
        
        return Response(listpost)
        # auth = get_authorization_header(request).split()

        # if auth and len(auth) == 2:
        #     token = auth[1].decode('utf-8')
        #     id = decode_access_token(token)

        #     user = User.objects.filter(pk=id).first()

        #     # data = request.data
        #     posts = Post.objects.all()
        #     serializer = PostSerializer(posts, many = True)
        #     return Response(serializer.data)

        # raise AuthenticationFailed('unauthenticated')

    def post(self, request, *args, **kwargs):
        auth = get_authorization_header(request).split()

        if auth and len(auth) == 2:
            token = auth[1].decode('utf-8')
            id = decode_access_token(token)

            data = {
                'user': id,
                'title': request.data.get('title'),
                'body': request.data.get('body')
            }
            serializer = PostSerializer(data = data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors)
            

        raise AuthenticationFailed('unauthenticated')

class PostDetailView(APIView):
    def get_object(self, pk):
        try:
            return Post.objects.get(pk = pk)
        except Post.DoesNotExist:
            return None
    
    def get(self, request, pk, *args, **kwargs):
        post = self.get_object(pk)
        if post is None:
            return Response({'error': 'Post not found'})
        serializer = PostSerializer(post)
        return Response(serializer.data)

    def put(self, request, pk, *args, **kwargs):
        post = self.get_object(pk)

        auth = get_authorization_header(request).split()

        if auth and len(auth) == 2:
            token = auth[1].decode('utf-8')
            id = decode_access_token(token)

            data = {
                'user': id,
                'title': request.data.get('title'),
                'body': request.data.get('body')
            }
            serializer = PostSerializer(post, data=data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors)
        raise AuthenticationFailed('unauthenticated')

    def delete(self, request, pk):
        post = self.get_object(pk)
        auth = get_authorization_header(request).split()

        if auth and len(auth) == 2:
            token = auth[1].decode('utf-8')
            id = decode_access_token(token)

            # data = {
            #     'user': id,
            #     'title': request.data.get('title'),
            #     'body': request.data.get('body')
            # }
            # print(id)
        # serializer = PostSerializer(post, data=data)
            if post is None:
                return Response({'error': 'Post not found'}, status = status.HTTP_404_NOT_FOUND)
            if post.user.id == id:
                post.delete()
                return Response({"res": "Object deleted!"}, status = status.HTTP_200_OK)
            return Response({"error": "You are not authorized to delete this post"}, status = status.HTTP_401_UNAUTHORIZED)
        raise AuthenticationFailed('unauthenticated')
