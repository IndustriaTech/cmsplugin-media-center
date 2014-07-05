from django.shortcuts import render


def picture_view(request, category=None):
    page = request.current_page
    context = {}
    if category:
        context.update({
            'category': category,
        })
    return render(request, page.get_template(), context)
