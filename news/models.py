from django.db import models

class News(models.Model):
    title = models.CharField(max_length=250)
    image = models.ImageField(upload_to="news_images/")
    description = models.TextField()
    created_at = models.DateField()

    def __str__(self):
        return self.title



class NewsImage(models.Model):
    news = models.ForeignKey(News, on_delete=models.CASCADE, related_name="news_images")
    image = models.ImageField(upload_to="news_images_list/")

    def __str__(self):
        return str(self.news.title)