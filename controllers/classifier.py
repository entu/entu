from boFunctions import *
from models import *
from forms import *


class DisplayClassifiers(webapp.RequestHandler):
    def get(self, url):
        classifiers = db.Query(Classifier).fetch(1000)
        form = ClassifiersForm()
        boView(self, '', 'classifiers.html', {'classifiers':classifiers, 'form':form})

    def post(self, url):
        form = ClassifiersForm(self.request.POST)

        if form.validate():
            classifier = db.Query(Classifier).filter('name = ', form.name.data ).get()

            if not classifier:
                classifier = Classifier()
                classifier.name = form.name.data

            if form.values.data != '':
                classifier.values =  boStrToList(form.values.data)
                classifier.save()
            else:
                classifier.delete()


        self.redirect('')



def main():
    boWSGIApp([
            (r'/classifier(.*)', DisplayClassifiers),
        ])


if __name__ == '__main__':
    main()