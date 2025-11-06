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


class PieceDragLog(models.Model):
    piece_id = models.CharField(max_length=50)
    x = models.FloatField()
    y = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=False)

    def __str__(self):
        return f"Piece {self.piece_id} is dragged to ({self.x}, {self.y}) at {self.timestamp}. {self.success}"


class PersonalRecordDetail(models.Model):
    detail_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20)
    puzzle_id = models.CharField(max_length=50)
    piece_id = models.CharField(max_length=5)
    action = models.CharField(max_length=50) # start, piece matched, completed, terminated
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.puzzle_id} - {self.piece_id} - {self.action}"


class PersonalRecordGeneral(models.Model):
    record_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20)
    team_member = models.CharField(max_length=255)
    game_mode = models.CharField(max_length=20)
    difficulty = models.CharField(max_length=20)
    character = models.CharField(max_length=20)
    activity = models.CharField(max_length=20)
    with_ai = models.BooleanField()
    puzzle_amount = models.IntegerField()
    time_start = models.DateTimeField(auto_now_add=False)
    time_end = models.DateTimeField(auto_now_add=False)
    solved_puzzle_amount = models.IntegerField()
    correct_piece_amount = models.IntegerField()
    wrong_piece_amount = models.IntegerField()
    accuracy = models.FloatField()

    def __str__(self):
        return f"{self.name} - {self.time_start} to {self.time_end} - {self.puzzle_amount} puzzles"

