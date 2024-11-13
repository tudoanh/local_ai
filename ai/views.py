from django.shortcuts import render


class HomeView:
    def get(self, request):
        return render(request, "home.html")
