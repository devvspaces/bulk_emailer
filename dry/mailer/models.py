from django.db import models


class Uploads(models.Model):
    """
    Model to save files uploaded to storage

    :param models: Model
    :type models: models.Model
    :return: Uploads
    :rtype: models.Model
    """
    file = models.FileField()

    def __str__(self):
        return self.file.name
