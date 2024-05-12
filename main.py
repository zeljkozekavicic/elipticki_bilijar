import pygame
import pymunk
import pymunk.pygame_util
import math
import numpy as np


#window variables
SCREEN_WIDTH = 1200 
SCREEN_HEIGHT = 678
BOTTOM_PANEL = 50

#colors
BG = (10, 205, 0)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)


# def run_title_screen():
#     screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
#     pygame.display.set_caption("My Pool Game")

#     font = pygame.font.Font(None, 36)
#     title_text = font.render("Welcome to My Pool Game", True, WHITE)

#     running = True
#     while running:
#         for event in pygame.event.get():
#             if event.type == pygame.QUIT:
#                 pygame.quit()
#                 quit()

#             if event.type == pygame.KEYDOWN:
#                 if event.key == pygame.K_RETURN:  # Start game on Enter key press
#                     running = False

#         screen.fill(BLACK)
#         screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 250))
#         pygame.display.flip()

#     # Start the main game loop after title screen
#     # You would call your main game function here
#     # For example, main_game_loop()



pygame.init()
#fonts
font = pygame.font.SysFont("Roboto", 50)
large_font = pygame.font.SysFont("Roboto", 70)


#game window
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT + BOTTOM_PANEL))
pygame.display.set_caption("Elipticki bilijar")

#pymunk space
space = pymunk.Space()
static_body = space.static_body
draw_options = pymunk.pygame_util.DrawOptions(screen)

#clock
clock = pygame.time.Clock()
FPS = 120

#game variables
lives = 3
score = 0
dia = 36
pocket_dia = 66
force = 0
max_force = 10000
force_direction = 1
game_running = True
cue_ball_potted = False
taking_shot = True
powering_up = False
potted_balls = []
ellipse_size = 0.8
ellipse_a = 0.7*SCREEN_WIDTH/2 * ellipse_size
ellipse_b = SCREEN_HEIGHT/2 * ellipse_size
ellipse_center = (SCREEN_WIDTH/2, SCREEN_HEIGHT/2)
focal_points = []
num_cushions = 300
outer_bound = (-200, -200)



#loading images
cue_image = pygame.image.load("assets/images/cue.png").convert_alpha()
table_image = pygame.image.load("assets/images/el_table2.png").convert_alpha()
ball_images = []

for i in range(1, 5):
   ball_image = pygame.image.load(f"assets/images/b{i}.png").convert_alpha()
   ball_images.append(ball_image)

#text rendering
def draw_text(text, font, text_col, x, y):
  img = font.render(text, True, text_col)
  screen.blit(img, (x, y))

#function for creating balls
def create_ball(radius, pos):
  body = pymunk.Body()
  body.position = pos
  shape = pymunk.Circle(body, radius)
  shape.mass = 3.8
  shape.elasticity = 0.8
  shape.collision_type = 1  
  pivot = pymunk.PivotJoint(static_body, body, (0, 0), (0, 0))
  pivot.max_bias = 0 
  pivot.max_force = 1000 
  
  space.add(body, shape, pivot)
  return shape

#calculating focal points
c_val = math.sqrt((ellipse_a)**2 - (ellipse_b)**2)  
focal_points.append((ellipse_center[0] + c_val, ellipse_center[1]))
focal_points.append((ellipse_center[0] - c_val, ellipse_center[1]))
pocket = focal_points[1]


#creating balls
balls = []
def create_balls(diam):
  red_ball  = create_ball(diam/2, (ellipse_center[0] + c_val, ellipse_center[1] - diam ))
  red_ball.type = "red"
  yellow_ball  = create_ball(diam/2, (ellipse_center[0] + c_val, ellipse_center[1] + diam))
  yellow_ball.type = "yellow"
  black_ball = create_ball(diam/2, (ellipse_center[0] + c_val, ellipse_center[1]))
  black_ball.type = "black"
  cue_ball = create_ball(diam/2, (ellipse_center[0], ellipse_center[1]))
  cue_ball.type = "cue"

  balls.append(red_ball)
  balls.append(yellow_ball)
  balls.append(black_ball)
  balls.append(cue_ball)
  
create_balls(dia)


#creating focal point attributes for balls
for ball in balls:
    ball.focal_point_passed = False
    ball.focal_shot_achieved = False 

#creating cushion (ellipse approx)
def sample_points_on_ellipse(a, b, num_points):
  t = np.linspace(0, 2*np.pi, num_points)
  x = a * np.cos(t)
  y = b * np.sin(t)
  return x, y

x, y = sample_points_on_ellipse(ellipse_a, ellipse_b, num_cushions)

def create_cushion(a, b):
  body = pymunk.Body(body_type = pymunk.Body.STATIC)
  body.position = (SCREEN_WIDTH/2,SCREEN_HEIGHT/2)
  shape = pymunk.Segment(body, a, b, 4)
  shape.elasticity = 0.8
  shape.friction = 0.796
  shape.collision_type = 2
  shape.color = (90, 160, 44, 0)
  
  space.add(body, shape)
  space.damping=0.15#bug

for i in range(0, num_cushions):
  create_cushion((x[i], y[i]), (x[(i+1) % num_cushions], y[(i+1) % num_cushions]))



#vector calculation
def is_point_passed(ball_position, focal_point, radius):
    distance = ((ball_position[0] - focal_point[0]) ** 2 + (ball_position[1] - focal_point[1]) ** 2) ** 0.5
    return distance <= radius

def normalize(vector):
    return vector / np.linalg.norm(vector)

def calculate_focal_shot(impact_point, current_velocity):
  intensity = np.linalg.norm(impact_point-current_velocity)
  normalized_shot_vector = np.array(normalize(np.subtract(impact_point, focal_points[1])))
  focal_shot_vector = 0.5*intensity * normalized_shot_vector
  # print(focal_shot_vector)
  return (focal_shot_vector[0],focal_shot_vector[1])

#ball-cushion collision handling
collision_type_ball = 1
collision_type_cushion = 2

def ball_cushion_collision_handler(arbiter, space, data):
    ball, cushion = arbiter.shapes
    # print("cushion hit!")
    #print(ball.body.velocity)
    if ball.collision_type == collision_type_ball and cushion.collision_type == collision_type_cushion:
        if ball.focal_point_passed:
            #print("focal shot!")
            ball.focal_point_passed = False
            ball.focal_shot_achieved = True
    return True 

def ball_cushion_collision_post_solve(arbiter, space, data):
    ball, cushion = arbiter.shapes

    if ball.focal_shot_achieved == True:
      # print("FOCAL SHOT ACTION!")
      impact_point = arbiter.contact_point_set.points[0].point_a
      # print("****impact****")
      # print(impact_point)
      # print("****vector****")
      # print(ball.body.velocity) 
      current_velocity = ball.body.velocity
      # print(np.linalg.norm(impact_point-current_velocity))
      ball.body.velocity = calculate_focal_shot(impact_point, current_velocity)
      ball.focal_shot_achieved = False

    return True

handler = space.add_collision_handler(collision_type_ball, collision_type_cushion)
handler.begin = ball_cushion_collision_handler
handler.post_solve = ball_cushion_collision_post_solve

#resolving score after ball has been potted
def ball_score_calculation(ball_type):
    ball_count = len(balls)
    if ball_type == "cue":
        return (4-lives)*(-5)
    if ball_count > 2 and ball_type=="black":
        return -5
    if ball_count == 4:
        if ball_type == "yellow":
            return 20
        else:
            return 10
    if ball_count == 3:
        if ball_type == "red":
            return 20
        else:
            return 10
    if ball_count <= 2:
        if ball_type == "red" or ball_type == "yellow":
            return 5
        else:
            return 20

#creating pool cue
class Cue():
  def __init__(self, pos):
    self.original_image = cue_image
    self.angle = 0
    self.image = pygame.transform.rotate(self.original_image, self.angle)
    self.rect = self.image.get_rect()
    self.rect.center = pos

  def update(self, angle):
    self.angle = angle

  def draw(self, surface):
    self.image = pygame.transform.rotate(self.original_image, self.angle)
    surface.blit(self.image,
      (self.rect.centerx - self.image.get_width() / 2,
      self.rect.centery - self.image.get_height() / 2)
     )

cue = Cue(balls[-1].body.position)

#creating power bars to show how hard the cue ball will be hit
power_bar = pygame.Surface((10, 20))
power_bar.fill(RED)

#game loop
run = True
while run:

  clock.tick(FPS)
  space.step(1 / FPS)

  screen.fill(BG)

  #draw pool table
  screen.blit(table_image, (0, 0))

  #check if any balls have been potted
  for i, ball in enumerate(balls):
    ball_x_dist = abs(ball.body.position[0] - pocket[0])
    ball_y_dist = abs(ball.body.position[1] - pocket[1])
    ball_dist = math.sqrt((ball_x_dist ** 2) + (ball_y_dist ** 2))
    if ball_dist <= pocket_dia / 2:
      score += ball_score_calculation(ball.type)
      #check if the potted ball was the cue ball
      if i == len(balls) - 1:
        lives -= 1
        cue_ball_potted = True
        ball.body.position = (ellipse_center[0], ellipse_center[1])
        ball.body.velocity = (0.0, 0.0)
      else:
        ball.body.position = outer_bound
        space.remove(ball.body)
        balls.remove(ball)
        potted_balls.append(ball_images[i])
        ball_images.pop(i)

  for ball in balls:
    if is_point_passed(ball.body.position, focal_points[0], 10):
      # print("focal point passed!")
      ball.focal_point_passed = True

  #drawing pool balls
  for i, ball in enumerate(balls):
    screen.blit(ball_images[i], (ball.body.position[0] - ball.radius, ball.body.position[1] - ball.radius))

  #check if all the balls have stopped moving
  taking_shot = True
  for ball in balls:
    if int(ball.body.velocity[0]) != 0 or int(ball.body.velocity[1]) != 0:
      taking_shot = False

  #drawing pool cue
  if taking_shot == True and game_running == True:
    if cue_ball_potted == True:
      #reposition cue ball
      balls[-1].body.position = (ellipse_center[0],ellipse_center[1])
      cue_ball_potted = False
    #calculating pool cue angle
    mouse_pos = pygame.mouse.get_pos()
    cue.rect.center = balls[-1].body.position
    x_dist = balls[-1].body.position[0] - mouse_pos[0]
    y_dist = -(balls[-1].body.position[1] - mouse_pos[1]) # -ve because pygame y coordinates increase down the screen
    cue_angle = math.degrees(math.atan2(y_dist, x_dist))
    cue.update(cue_angle)
    cue.draw(screen)

  #powering up pool cue
  if powering_up == True and game_running == True:
    force += 200 * force_direction
    if force >= max_force or force <= 0:
      force_direction *= -1
    #drawing power bars
    for b in range(math.ceil(force / 2000)):
      screen.blit(power_bar,
       (balls[-1].body.position[0] - 30 + (b * 15),
        balls[-1].body.position[1] + 30))
  elif powering_up == False and taking_shot == True:
    x_impulse = math.cos(math.radians(cue_angle))
    y_impulse = math.sin(math.radians(cue_angle))
    balls[-1].body.apply_impulse_at_local_point((force * -x_impulse, force * y_impulse), (0, 0))
    force = 0
    force_direction = 1

  #drawing bottom panel
  PANEL = (6, 186, 111)
  pygame.draw.rect(screen, PANEL, (0, SCREEN_HEIGHT, SCREEN_WIDTH, BOTTOM_PANEL))
  draw_text("Lives: " + str(lives), font, BLACK, SCREEN_WIDTH - 170, SCREEN_HEIGHT + 15)
  draw_text("Score: " + str(score), font, BLACK, SCREEN_WIDTH - 350, SCREEN_HEIGHT + 15)

  #drawing potted balls in bottom panel
  for i, ball in enumerate(potted_balls):
    screen.blit(ball, (10 + (i * 50), SCREEN_HEIGHT + 10))

  #checking for game over
  if lives <= 0:
    draw_text("GAME OVER", large_font, BLACK, SCREEN_WIDTH / 2-150, SCREEN_HEIGHT / 2 - 75)
    game_running = False

  #check if all balls are potted
  if len(balls) == 1:
    draw_text("YOU WON! Score: "+str(score), large_font, BLACK, SCREEN_WIDTH / 2-200, SCREEN_HEIGHT / 2 - 75)
    game_running = False

  #event handler
  for event in pygame.event.get():
    if event.type == pygame.MOUSEBUTTONDOWN and taking_shot == True:
      powering_up = True
    if event.type == pygame.MOUSEBUTTONUP and taking_shot == True:
      powering_up = False
    if event.type == pygame.QUIT:
      run = False

  #space.debug_draw(draw_options)
  pygame.display.update()

pygame.quit()

