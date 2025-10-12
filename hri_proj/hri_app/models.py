from django.db import models

# Create your models here.
class PuzzleImage(models.Model):
    img_id = models.CharField(max_length=32, primary_key=True) # UUID4
    img_path = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.img_id} - {self.img_path}"

class PuzzlePiece(models.Model):
    piece_id = models.AutoField(primary_key=True)
    puzzle_image = models.ForeignKey(PuzzleImage, related_name='pieces', on_delete=models.CASCADE)
    piece_number = models.IntegerField()
    piece_path = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.piece_id} - Piece {self.piece_number} - ({self.piece_path})"