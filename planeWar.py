import pygame  # 导入动态模块(.dll .pyd .so) 不需要在包名后边跟模块名
from pygame.locals import *
import time
import random
import sys

# 定义常量(定义后,不再改值)
WINDOW_HEIGHT = 768
WINDOW_WIDTH = 512

enemy_list = []
score = 0
is_restart = False


class Map:
    def __init__(self, img_path, window):
        self.x = 0
        self.bg_img1 = pygame.image.load(img_path)
        self.bg_img2 = pygame.image.load(img_path)
        self.bg1_y = - WINDOW_HEIGHT
        self.bg2_y = 0
        self.window = window

    def move(self):
        # 当地图1的 y轴移动到0，则重置
        if self.bg1_y >= 0:
            self.bg1_y = - WINDOW_HEIGHT

        # 当地图2的 y轴移动到 窗口底部，则重置
        if self.bg2_y >= WINDOW_HEIGHT:
            self.bg2_y = 0

        # 每次循环都移动1个像素
        self.bg1_y += 3
        self.bg2_y += 3

    def display(self):
        """贴图"""
        self.window.blit(self.bg_img1, (self.x, self.bg1_y))
        self.window.blit(self.bg_img2, (self.x, self.bg2_y))


class HeroBullet:
    """英雄子弹类"""
    def __init__(self, img_path, x, y, window):
        self.img = pygame.image.load(img_path)
        self.x = x
        self.y = y
        self.window = window

    def display(self):
        self.window.blit(self.img, (self.x, self.y))

    def move(self):
        """向上飞"""
        self.y -= 10

    def is_hit_enemy(self, enemy):
        if pygame.Rect.colliderect(
            pygame.Rect(self.x, self.y, 20, 31),
            pygame.Rect(enemy.x, enemy.y, 100, 68)
        ):  # 判断是否交叉
            return True
        else:
            return False


class EnemyPlane:
    """敌人飞机类"""
    def __init__(self, img_path, x, y, window):
        self.img = pygame.image.load(img_path)  # 图片对象
        self.x = x  # 飞机坐标
        self.y = y
        self.window = window  # 飞机所在的窗口
        self.is_hited = False
        self.anim_index = 0
        self.hit_sound = pygame.mixer.Sound("res/baozha.ogg")

    def move(self):
        self.y += 10
        # 到达窗口下边界,回到顶部
        if self.y >= WINDOW_HEIGHT:
            self.x = random.randint(0, random.randint(0, WINDOW_WIDTH - 100))
            self.y = 0

    def plane_down_anim(self):
        """敌机被击中动画"""
        if self.anim_index >= 21:  # 动画执行完
            self.anim_index = 0
            self.img = pygame.image.load("res/img-plane_%d.png" % random.randint(1, 7))
            self.x = random.randint(0, WINDOW_WIDTH - 100)
            self.y = 0
            self.is_hited = False
            return
        elif self.anim_index == 0:
            self.hit_sound.play()
        self.img = pygame.image.load("res/bomb-%d.png" % (self.anim_index // 3 + 1))
        self.anim_index += 1



    def display(self):
        """贴图"""
        if self.is_hited:
            self.plane_down_anim()

        self.window.blit(self.img, (self.x, self.y))


class HeroPlane:
    def __init__(self, img_path, x, y, window):
        self.img = pygame.image.load(img_path)  # 图片对象
        self.x = x  # 飞机坐标
        self.y = y
        self.window = window  # 飞机所在的窗口
        self.bullets = []  # 记录该飞机发出的所有子弹
        self.is_hited = False
        self.is_anim_down = False
        self.anim_index = 0

    def is_hit_enemy(self, enemy):
        if pygame.Rect.colliderect(
            pygame.Rect(self.x, self.y, 120, 78),
            pygame.Rect(enemy.x, enemy.y, 100, 68)
        ):  # 判断是否交叉
            return True
        else:
            return False

    def plane_down_anim(self):
        """敌机被击中动画"""
        if self.anim_index >= 21:  # 动画执行完
            self.is_hited = False
            self.is_anim_down = True
            return

        self.img = pygame.image.load("res/bomb-%d.png" % (self.anim_index // 3 + 1))
        self.anim_index += 1

    def display(self):
        """贴图"""
        for enemy in enemy_list:
            if self.is_hit_enemy(enemy):
                enemy.is_hited = True
                self.is_hited = True
                self.plane_down_anim()
                break

        self.window.blit(self.img, (self.x, self.y))

    def display_bullets(self):
        # 贴子弹图
        deleted_bullets = []

        for bullet in self.bullets:
            # 判断 子弹是否超出 上边界
            if bullet.y >= -31:  # 没有出边界
                bullet.display()
                bullet.move()
            else:  # 飞出边界
                deleted_bullets.append(bullet)

            for enemy in enemy_list:
                if bullet.is_hit_enemy(enemy):  # 判断是否击中敌机
                    enemy.is_hited = True
                    deleted_bullets.append(bullet)
                    global score
                    score += 10
                    break

        for out_window_bullet in deleted_bullets:
            self.bullets.remove(out_window_bullet)

    def move_left(self):
        """往左飞"""
        if self.x >= 0 and not self.is_hited:
            self.x -= 5

    def move_right(self):
        """往右飞"""
        if self.x <= WINDOW_WIDTH - 120 and not self.is_hited:
            self.x += 5

    def move_up(self):
        """往上飞"""
        if self.y >= 0 and not self.is_hited:
            self.y -= 5

    def move_down(self):
        """往下飞"""
        if self.y <= WINDOW_HEIGHT - 78 and not self.is_hited:
            self.y += 5

    def fire(self):
        """发射子弹"""
        # 创建子弹对象  子弹x = 飞机x + 飞机宽度的一半 - 子弹宽度的一半
        bullet = HeroBullet("res/bullet_9.png", self.x + 60 - 10, self.y - 31, self.window)
        # 显示子弹(贴子弹图)
        bullet.display()
        self.bullets.append(bullet)  # 为了避免子弹对象被释放(只有局部变量引用对象,方法一执行完就会释放)


class Game:
    def __init__(self):
        pygame.init()
        # 设置标题
        pygame.display.set_caption("飞机大战 v1.0")
        # 设置图标
        game_ico = pygame.image.load("res/app.ico")
        pygame.display.set_icon(game_ico)
        pygame.mixer.music.load("res/bg2.ogg")
        # 游戏结束的音效（超级玛丽）
        self.gameover_sound = pygame.mixer.Sound("res/gameover.wav")
        # 循环播放背景音乐
        pygame.mixer.music.play(-1)
        # 创建窗口  set_mode((窗口尺寸))
        self.window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        # 创建地图对象
        self.game_map = Map("res/img_bg_level_%d.jpg" % random.randint(1, 5), self.window)
        # 创建对象
        self.hero_plane = HeroPlane("res/hero2.png", 240, 500, self.window)
        enemy_plane1 = EnemyPlane("res/img-plane_%d.png" % random.randint(1, 7), random.randint(0, WINDOW_WIDTH - 100), 0, self.window)
        enemy_plane2 = EnemyPlane("res/img-plane_%d.png" % random.randint(1, 7), random.randint(0, WINDOW_WIDTH - 100), random.randint(-150, -68),
                                  self.window)
        enemy_plane3 = EnemyPlane("res/img-plane_%d.png" % random.randint(1, 7), random.randint(0, WINDOW_WIDTH - 100), random.randint(-300, -140),
                                  self.window)
        enemy_list.append(enemy_plane1)
        enemy_list.append(enemy_plane2)
        enemy_list.append(enemy_plane3)
        self.enemy_list = enemy_list
        # 创建文字对象
        # self.score_font = pygame.font.SysFont("simhei", 40)
        self.score_font = pygame.font.Font("res/SIMHEI.TTF", 40)

    def draw_text(self, content, size, x, y):
        # font_obj = pygame.font.SysFont("simhei", size)
        font_obj = pygame.font.Font("res/SIMHEI.TTF", size)
        text = font_obj.render(content, 1, (255, 255, 255))
        self.window.blit(text, (x, y))

    def wait_game_input(self):
        while True:
            for event in pygame.event.get():
                if event.type == QUIT:
                    sys.exit()
                    pygame.quit()
                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        sys.exit()
                        pygame.quit()
                    elif event.key == K_RETURN:
                        global is_restart, score
                        is_restart = True
                        score = 0
                        return

    def game_start(self):
        # 贴背景图片
        self.game_map.display()
        self.draw_text("飞机大战", 40, WINDOW_WIDTH / 2 - 100, WINDOW_HEIGHT / 3)
        self.draw_text("按Enter开始游戏, Esc退出游戏.", 28, WINDOW_WIDTH /3 - 140, WINDOW_HEIGHT /2)
        pygame.display.update()
        self.wait_game_input()

    def game_over(self):
        # 先停止背景音乐
        pygame.mixer.music.stop()
        # 再播放音效
        self.gameover_sound.play()
        # 贴背景图片
        self.game_map.display()
        self.draw_text("战机被击落,得分为 %d" % score, 28, WINDOW_WIDTH / 3 - 100, WINDOW_HEIGHT / 3)
        self.draw_text("按Enter重新开始, Esc退出游戏.", 28, WINDOW_WIDTH / 3 - 140, WINDOW_HEIGHT / 2)
        pygame.display.update()
        self.wait_game_input()
        self.gameover_sound.stop()

    def key_control(self):
        # 获取事件，比如按键等  先显示界面,再根据获取的事件,修改界面效果
        for event in pygame.event.get():
            # 判断是否是点击了退出按钮
            if event.type == QUIT:
                sys.exit()  # 让程序终止
                pygame.quit()
            # 判断是否是按下了键
            elif event.type == KEYDOWN:
                # 检测按键是否是空格键
                if event.key == K_SPACE:
                    self.hero_plane.fire()
        # 获取连续按下的情况
        pressed_keys = pygame.key.get_pressed()
        if pressed_keys[pygame.K_LEFT]:
            self.hero_plane.move_left()

        if pressed_keys[pygame.K_RIGHT]:
            self.hero_plane.move_right()

        if pressed_keys[pygame.K_UP]:
            self.hero_plane.move_up()

        if pressed_keys[pygame.K_DOWN]:
            self.hero_plane.move_down()

    def display(self):
        # 贴背景图
        self.game_map.display()
        self.game_map.move()
        # 贴飞机图
        self.hero_plane.display()
        self.hero_plane.display_bullets()
        # 贴敌机图
        for enemy in enemy_list:
            enemy.display()
            # 让敌机移动
            if not enemy.is_hited:
                enemy.move()
        # 贴得分文字
        score_text = self.score_font.render("得分:%d" % score, 1, (255, 255, 255))
        self.window.blit(score_text, (10, 10))
        # 刷新界面  不刷新不会更新显示的内容
        pygame.display.update()

    def run(self):
        if is_restart == False:
            self.game_start()
        while True:
            # 显示界面
            self.display()
            if self.hero_plane.is_anim_down:
                self.hero_plane.is_anim_down = False
                global enemy_list
                enemy_list = []
                break
            # 键盘控制
            self.key_control()
            # 每次循环,让程序休眠一会儿
            time.sleep(0.01)
        self.game_over()


def main():
    """主函数  一般将程序的入口"""
    # 运行游戏
    while True:
        # 创建游戏对象
        game = Game()
        game.run()

if __name__ == '__main__':  # 判断是否主动执行该文件
    main()