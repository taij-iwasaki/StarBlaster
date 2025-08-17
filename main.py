import pygame as pg
import sys,time,random,asyncio

#pip install pygame

# ゲーム設定
ENEMY_STOP_SCORE = 50 
BOSS01_HP = 50  # 敵の出現を停止するスコア

setting_dict = {
    "explosion_interval":0.3,
    "shooting_interval":0.5,
    "star_blaster_speed":8
}

class starBlaster():
    def __init__(self,screen):
        self.star_blaster = pg.image.load("images/star_blaster.png")
        self.star_blaster = pg.transform.scale(self.star_blaster,(50,50))
        self.screen = screen
        self.rect = pg.Rect(400, 650, 50, 70)
        self.is_alive = True  # Xwingの生存状態

    def update(self):
        if not self.is_alive:
            return  # 死亡時は更新しない

        self.key = pg.key.get_pressed()
        speed = setting_dict["star_blaster_speed"]  # 移動量

        # 右移動
        if self.key[pg.K_RIGHT]:
            if self.rect.right + speed <= 800:  # 画面右端は800
                self.rect.x += speed

        # 左移動
        if self.key[pg.K_LEFT]:
            if self.rect.left - speed >= 0:  # 画面左端は0
                self.rect.x -= speed

        # 上移動
        if self.key[pg.K_UP]:
            if self.rect.top - speed >= 0:
                self.rect.y -= speed

        # 下移動
        if self.key[pg.K_DOWN]:
            if self.rect.bottom + speed <= 800:  # 画面下端は800
                self.rect.y += speed

        self.screen.blit(self.star_blaster, self.rect)
    
    def check_collision(self, enemy_rects, enemy_beams):
        """敵や敵のビームとの衝突判定（実際のrectの2/3で判定）"""
        if not self.is_alive:
            return False

        # 判定用にrectを縮小
        collision_rect = self.rect.copy()
        shrink_w = collision_rect.width * 1 / 2
        shrink_h = collision_rect.height * 1 / 2
        collision_rect.width = shrink_w
        collision_rect.height = shrink_h
        # 中心を元のrectに合わせる
        collision_rect.center = self.rect.center

        # 敵との衝突判定
        for enemy_rect in enemy_rects:
            if collision_rect.colliderect(enemy_rect):
                print("Xwingが敵に衝突しました！")
                self.is_alive = False
                return True

        # 敵のビームとの衝突判定
        for beam in enemy_beams:
            if collision_rect.colliderect(beam['rect']):
                print("Xwingが敵のビームに衝突しました！")
                self.is_alive = False
                return True

        return False
    
    def get_collision_position(self):
        """衝突時の位置を取得（爆発エフェクト用）"""
        return self.rect
    
    def get_rect(self):
        return self.rect

class XwingBeam:
    def __init__(self, screen):
        self.image = pg.image.load("images/beam_xwing.png")
        self.image = pg.transform.scale(self.image, (10, 20))
        self.screen = screen
        self.rects = []  # 発射中の弾を格納するリスト
        self.last_shoot_time = 0  # 最後に撃った時間
        self.score = 0

    def update(self, xwing_rect):
        keys = pg.key.get_pressed()
        current_time = time.time()

        # 1秒おきに新しい弾を発射
        if keys[pg.K_SPACE] and (current_time - self.last_shoot_time >= setting_dict["shooting_interval"]):
            pg.mixer.Sound("musics/beam01.ogg").play()
            beam_rect = self.image.get_rect()
            beam_rect = self.image.get_rect()
            beam_rect.centerx = xwing_rect.centerx
            beam_rect.bottom = xwing_rect.top 
            self.rects.append(beam_rect)
            self.last_shoot_time = current_time

        for rect in self.rects:
            rect.y -= 10
            self.screen.blit(self.image, rect)

        # 画面外に出た弾を削除
        self.rects = [rect for rect in self.rects if rect.bottom > 0]

    def checkt_touch(self, enemy_rects):
        if enemy_rects != []:
            print(f"敵の数: {len(enemy_rects)}, ビームの数: {len(self.rects)}")
            # 衝突したビームを削除
            for enemy_rect in enemy_rects:
                for beam_rect in self.rects:
                    collision = beam_rect.colliderect(enemy_rect)
                    print(f"ビーム衝突判定: {collision}")
                    if collision:
                        #########
                        pg.mixer.Sound("musics/explosion.ogg").play()
                        #########
                        print("ビームが敵に当たりました！ビームを削除します")
                        self.score += 1
                        print(f"削除前のビーム数: {len(self.rects)}")
                        # 衝突したビームを削除
                        self.rects = [beam for beam in self.rects 
                                    if not beam.colliderect(enemy_rect)]
                        print(f"ビーム削除後、残りビーム数: {len(self.rects)}")

    def get_rects(self):
        return self.rects
    
    def get_score(self):
        return self.score
    
    def reset_score(self):
        """スコアを0にリセット"""
        self.score = 0
        print("スコアをリセットしました")


class enemy01:
    def __init__(self, screen):
        self.image = pg.image.load("images/zako01.png")
        self.image = pg.transform.scale(self.image, (100, 100))
        self.screen = screen
        self.rects = []  # 敵のリスト
        self.last_appear_time = 0  # 最後に敵を生成した時間
        self.xwing_beam = XwingBeam(self.screen)
        self.collided_enemies = []
        
        # 敵のビーム用
        self.enemy_beams = []  # 敵のビームリスト
        self.last_beam_time = 0  # 最後にビームを撃った時間
        
        # 赤い丸のビーム画像を作成
        self.beam_image = pg.Surface((8, 8))  # 8x8のSurface
        self.beam_image.fill((255, 0, 0))  # 赤色で塗りつぶし

    def update(self, xwing_rect=None, score=0):
        keys = pg.key.get_pressed()
        current_time = time.time()
        
        # スコアがENEMY_STOP_SCORE未満の場合のみ敵を生成
        if score < ENEMY_STOP_SCORE:
            x = random.randint(20,600)
            rect = pg.Rect(x, 0, 100, 100)
            
            if current_time - self.last_appear_time >= 0.5:
                self.rects.append(rect)
                self.last_appear_time = current_time
        else:
            print(f"スコア{ENEMY_STOP_SCORE}達成！敵の生成を停止します")
        
        # 敵のビーム発射（Xwingの位置が渡された場合、スコアENEMY_STOP_SCORE未満の場合のみ）
        if xwing_rect and current_time - self.last_beam_time >= 1.0 and score < ENEMY_STOP_SCORE:
            self.shoot_beam(xwing_rect)
            self.last_beam_time = current_time
        
        # 敵の描画
        for rect in self.rects:
            rect.y += 2
            self.screen.blit(self.image, rect)

        # 画面外に出た敵を削除
        self.rects = [rect for rect in self.rects if rect.bottom > 0]
        
        # 敵のビームの更新・描画
        self.update_beams()
    
    def shoot_beam(self, xwing_rect):
        """Xwingに向かってビームを発射"""
        if self.rects:  # 敵が存在する場合
            # ランダムに敵を選択
            enemy_rect = random.choice(self.rects)
            
            # ビームの初期位置（敵の中心）
            beam_rect = self.beam_image.get_rect()
            beam_rect.centerx = enemy_rect.centerx
            beam_rect.centery = enemy_rect.centery
            
            # Xwingへの方向を計算
            dx = xwing_rect.centerx - enemy_rect.centerx
            dy = xwing_rect.centery - enemy_rect.centery
            
            # 正規化して速度を設定
            distance = (dx**2 + dy**2)**0.5
            if distance > 0:
                speed = 3
                dx = (dx / distance) * speed
                dy = (dy / distance) * speed
            
            # ビーム情報を保存
            self.enemy_beams.append({
                'rect': beam_rect,
                'dx': dx,
                'dy': dy
            })
    
    def update_beams(self):
        """敵のビームの更新・描画"""
        # ビームの移動
        for beam in self.enemy_beams:
            beam['rect'].x += beam['dx']
            beam['rect'].y += beam['dy']
            self.screen.blit(self.beam_image, beam['rect'])
        
        # 画面外に出たビームを削除
        self.enemy_beams = [beam for beam in self.enemy_beams 
                           if 0 < beam['rect'].x < 800 and 0 < beam['rect'].y < 800]
    
    def checkt_touch(self,rects):
        if rects != []:
        # 衝突した敵を削除
            for beam_rect in rects:
                for my_rect in self.rects:
                    collision = beam_rect.colliderect(my_rect)
                    print(f"衝突判定: {collision}")
                    if collision:
                        print("衝突しました！敵を削除します")
                        self.collided_enemies.append(my_rect)
                        self.rects = [my_rect for my_rect in self.rects 
                                    if not beam_rect.colliderect(my_rect)]

    def get_rects(self):
        return self.rects
    
    def get_collided_enemies(self):
        return self.collided_enemies


class boss01():
    def __init__(self, screen):
        self.image = pg.image.load("images/boss.png")  # 後でボス用画像に変更可能
        self.image = pg.transform.scale(self.image, (200, 200))  # ボスは大きめ
        self.screen = screen
        self.rect = pg.Rect(400, 100, 150, 150)  # 画面中央上部に配置
        
        # ボスの状態
        self.hp = BOSS01_HP  # HP（50発当たったら消える）
        self.is_alive = True
        
        # 移動用
        self.dx = 2  # 左右移動の速度
        self.move_timer = 0  # 移動方向変更用タイマー
        
        # ビーム用
        self.beams = []  # ボスのビームリスト
        self.last_beam_time = 0  # 最後にビームを撃った時間
        self.beam_image = pg.Surface((12, 12))  # ボスのビーム画像
        self.beam_image.fill((255, 0, 255))  # マゼンタ色（敵と区別）
    
    def update(self, xwing_rect):
        if not self.is_alive:
            return
            
        current_time = time.time()
        v = random.randint(2,4)
        
        # 左右ランダム移動
        if current_time - self.move_timer > v:  # 2秒おきに方向変更
            self.dx = random.choice([-3, 3])  # -3または3をランダム選択
            self.move_timer = current_time
        
        # 移動実行
        self.rect.x += self.dx
        
        # 画面端で跳ね返り
        if self.rect.left < 0 or self.rect.right > 800:
            self.dx = -self.dx
        
        # ランダムなビーム発射（Xwingの方向に向かって）
        interval = random.randint(2,8)
        if current_time - self.last_beam_time >= interval/10: 
            self.shoot_beam(xwing_rect)
            self.last_beam_time = current_time
        
        # ボスの描画
        self.screen.blit(self.image, self.rect)
        
        # ビームの更新・描画
        self.update_beams()
    
    def shoot_beam(self, xwing_rect):
        """Xwingに向かってビームを発射（ランダムサイズ）"""
        # ビームの大きさをランダムに設定
        beam_width = random.randint(8, 25)
        beam_height = beam_width  # 丸にしたいので縦横同じ
        beam_image = pg.Surface((beam_width, beam_height), pg.SRCALPHA)

        # ビームの大きさに応じて色を決める
        if beam_width <= 10:
            color = (255, 0, 0)      # 赤
        elif beam_width <= 12:
            color = (255, 100, 0)    # オレンジ系
        elif beam_width <= 14:
            color = (255, 50, 50)    # ピンク系
        else:
            color = (200, 0, 0)      # ダークレッド

        pg.draw.circle(beam_image, color, (beam_width//2, beam_height//2), beam_width//2)

        # ビームの初期位置（ボスの中心）
        beam_rect = beam_image.get_rect()
        beam_rect.centerx = self.rect.centerx
        beam_rect.centery = self.rect.centery

        # Xwingへの方向を計算
        dx = xwing_rect.centerx - self.rect.centerx
        dy = xwing_rect.centery - self.rect.centery
        distance = (dx**2 + dy**2)**0.5
        if distance > 0:
            speed = 4
            dx = (dx / distance) * speed
            dy = (dy / distance) * speed

        # ビーム情報を保存
        self.beams.append({
            'rect': beam_rect,
            'dx': dx,
            'dy': dy,
            'image': beam_image  # ビームごとに別の画像を保持
        })
    
    def update_beams(self):
        """ボスのビームの更新・描画"""
        for beam in self.beams:
            beam['rect'].x += beam['dx']
            beam['rect'].y += beam['dy']
            self.screen.blit(beam['image'], beam['rect'])
        
        # 画面外に出たビームを削除
        self.beams = [beam for beam in self.beams 
                    if 0 < beam['rect'].x < 800 and 0 < beam['rect'].y < 800]
    
    def take_damage(self):
        """ダメージを受ける（HP減少）"""
        self.hp -= 1
        print(f"ボスHP: {self.hp}")
        
        if self.hp <= 0:
            self.is_alive = False
            print("ボス撃破！")
            return True  # 撃破されたことを示すフラグ
        return False
    
    def get_rect(self):
        return self.rect
    
    def get_beams(self):
        return self.beams

class destroyed():
    def __init__(self):
        self.image = pg.image.load("images/bakuhatsu.png")
        self.image = pg.transform.scale(self.image, (100, 100))
        self.effects = []
    
    def add_effect(self, rect, screen):
        current_time = time.time()
        self.effects.append({
            'rect': rect,
            'start_time': current_time,
            'screen': screen
        })
    
    def update_and_draw(self):
        current_time = time.time()
        print(f"更新前のエフェクト数: {len(self.effects)}")
        
        # 0.5秒経過したエフェクトを削除
        self.effects = [effect for effect in self.effects 
                       if current_time - effect['start_time'] < setting_dict["explosion_interval"]]
        
        print(f"更新後のエフェクト数: {len(self.effects)}")
        
        # 残っているエフェクトを描画
        for effect in self.effects:
            effect['screen'].blit(self.image, effect['rect'])

def show_game_over(screen):
    """GameOver画面を表示"""
    # フォントの初期化
    pg.font.init()
    font = pg.font.Font(None, 74)  # デフォルトフォント、サイズ74
    
    # GameOverテキストの作成
    text = font.render('GAME OVER', True, (255, 0, 0))  # 赤色
    text_rect = text.get_rect()
    text_rect.center = (400, 400)  # 画面中央
    
    # 背景を半透明の黒で覆う
    overlay = pg.Surface((800, 800))
    overlay.set_alpha(128)  # 半透明
    overlay.fill((0, 0, 0))
    
    # 描画
    screen.blit(overlay, (0, 0))
    screen.blit(text, text_rect)
    pg.mixer.music.set_volume(0.5)   # 音量 0.0～1.0
    pg.mixer.music.play(-1)    
    # リスタート案内
    # restart_font = pg.font.Font(None, 36)
    # restart_text = restart_font.render('Press R to Restart', True, (255, 255, 255))  # 白色
    # restart_rect = restart_text.get_rect()
    # restart_rect.center = (400, 500)
    # screen.blit(restart_text, restart_rect)

def show_start_screen(screen):
    """スタート画面を表示"""
    # フォントの初期化
    pg.font.init()
    title_font = pg.font.Font(None, 74)  # タイトル用フォント
    info_font = pg.font.Font(None, 36)   # 情報用フォント
    
    # タイトルテキストの作成
    title_text = title_font.render('Star Eyes', True, (255, 215, 0))  # 金色
    title_rect = title_text.get_rect()
    title_rect.center = (400, 200)  # 画面上部中央

    
    # 操作方法の説明
    font = pg.font.Font("JK-Maru-Gothic-M.otf", 20)
    controls_text = font.render('突如地球を奇襲した眼玉星人たち', True, (255, 255, 255))  # 白色
    controls_rect = controls_text.get_rect()
    controls_rect.center = (400, 300)
    
    move_text = font.render('だが地球には最強戦闘機「Star Blaster」をあやつる Yasui_Yasaiという傭兵がいた。', True, (255, 255, 255))
    move_rect = move_text.get_rect()
    move_rect.center = (400, 330)
    
    shoot_text = font.render('彼は眼玉星人を倒し地球を救えるのか', True, (255, 255, 255))
    shoot_rect = shoot_text.get_rect()
    shoot_rect.center = (400, 360)
    
    # ゲーム開始案内
    start_text = info_font.render('Press SPACE to Start', True, (0, 255, 0))  # 緑色
    start_rect = start_text.get_rect()
    start_rect.center = (400, 450)
    
    # 背景を半透明の黒で覆う
    overlay = pg.Surface((800, 800))
    overlay.set_alpha(180)  # 半透明
    overlay.fill((0, 0, 0))
    
    # 描画
    screen.blit(overlay, (0, 0))
    screen.blit(title_text, title_rect)
    screen.blit(controls_text, controls_rect)
    screen.blit(move_text, move_rect)
    screen.blit(shoot_text, shoot_rect)
    screen.blit(start_text, start_rect)

def show_clear_screen(screen, text="GAME CLEAR!"):
    """クリア画面を表示"""
    # フォントの初期化
    pg.font.init()
    font = pg.font.Font(None, 74)  # デフォルトフォント、サイズ74
    
    # クリアテキストの作成
    clear_text = font.render(text, True, (0, 255, 0))  # 緑色
    clear_rect = clear_text.get_rect()
    clear_rect.center = (400, 300)  # 画面中央
    
    # 背景を半透明の黒で覆う
    overlay = pg.Surface((800, 800))
    overlay.set_alpha(128)  # 半透明
    overlay.fill((0, 0, 0))
    
    # 描画
    screen.blit(overlay, (0, 0))
    screen.blit(clear_text, clear_rect)
    
    # リスタート案内
    restart_font = pg.font.Font(None, 36)
    restart_text = restart_font.render('You Killed all Eyes!!!!!', True, (255, 255, 255))  # 白色
    restart_rect = restart_text.get_rect()
    restart_rect.center = (400, 400)
    screen.blit(restart_text, restart_rect)

    
async def main():
    
    pg.init()
    screen = pg.display.set_mode((800,800))
    # 背景画像の読み込み
    try:
        background = pg.image.load("images/universe_space01.png")
        background = pg.transform.scale(background, (800, 800))  # 画面サイズに合わせてスケール
        use_background = True
        print("背景画像を読み込みました")
    except:
        background = None
        use_background = False
        print("背景画像が見つかりません。白背景を使用します")    
    
    star_blaster = starBlaster(screen) 
    xwing_beam = XwingBeam(screen)
    xwing_beam.update(star_blaster.get_rect())
    enemy = enemy01(screen)
    boss = boss01(screen)  # ボスのインスタンスを作成
    frame_counter = 0
    destroyed_effects = destroyed()  # 爆発エフェクトのインスタンスをループ外で作成

    playing_bgm_flg = False
    start_bgm_flg = False    
    fighting_boss = False
    end_effect_cnt = 0
    
    # ゲーム状態管理
    game_state = "START"  # START, PLAYING, GAME_OVER, CLEAR



    time.sleep(2)
    

    while True:
        # xwing_rect.x =xwing_rect.x + 1　　　
        await asyncio.sleep(0) 
        # ゲーム状態に応じた処理
        if game_state == "START":
            if start_bgm_flg == False :
                pg.mixer.music.load("musics/Begining.ogg") 
                pg.mixer.music.set_volume(1)   # 音量 0.0～1.0
                pg.mixer.music.play(-1)  
                start_bgm_flg = True
            # スタート画面の表示
            if use_background and background:
                screen.blit(background, (0, 0))
            else:
                screen.fill(pg.Color("white"))
            show_start_screen(screen)
            time.sleep(0.5)
            
        elif game_state == "PLAYING":
            if playing_bgm_flg == False:
                pg.mixer.music.load("musics/Fighting.ogg") 
                pg.mixer.music.set_volume(1)   # 音量 0.0～1.0
                pg.mixer.music.play(-1)  
                playing_bgm_flg = True
            # ゲームプレイ中の処理
            # 背景の描画
            if use_background and background:
                screen.blit(background, (0, 0))  # 背景画像を描画
            else:
                screen.fill(pg.Color("white"))  # 白背景を描画

            beam_rect = xwing_beam.get_rects()
            enemy_rect = enemy.get_rects()
            enemy_beams = enemy.enemy_beams  # 敵のビームリストを取得
            
            # Xwingの衝突判定
            if star_blaster.check_collision(enemy_rect, enemy_beams):
                # Xwingが衝突した場合、爆発エフェクトを追加
                destroyed_effects.add_effect(star_blaster.get_rect(), screen)
                print("Xwingが衝突しました！爆発エフェクトを表示")
                game_state = "GAME_OVER"
            
            enemy.checkt_touch(beam_rect)  # 衝突判定を呼び出す
            xwing_beam.checkt_touch(enemy_rect)  # 衝突判定を呼び出す
            star_blaster.update()
            enemy.update(star_blaster.get_rect(), xwing_beam.get_score())  # Xwingの位置とスコアを渡す
            xwing_beam.update(star_blaster.get_rect())
            
            # 描画処理
            # enemy.blt() と xwing_beam.blt() は不要（update内で描画済み）
            
            # 衝突した敵の位置に爆発エフェクトを追加
            collided_enemies = enemy.get_collided_enemies()
            for enemy_rect in collided_enemies:
                destroyed_effects.add_effect(enemy_rect, screen)
            
            # 衝突した敵のリストをクリア（重複追加を防ぐ）
            enemy.collided_enemies.clear()
            
            # 爆発エフェクトの更新・描画
            destroyed_effects.update_and_draw() 

            # ボスの処理（スコアがENEMY_STOP_SCOREを超えた場合のみ）
            if xwing_beam.get_score() > ENEMY_STOP_SCORE-1:
                if fighting_boss == False:
                    pg.mixer.music.load("musics/FightingBoss.ogg") 
                    pg.mixer.music.play(-1)  
                    fighting_boss = True
                if not boss.is_alive:  # まだ死んでる場合は復活させる
                    boss.is_alive = True
                boss.update(star_blaster.get_rect())
                
                # ボスとの衝突判定
                if star_blaster.check_collision([boss.get_rect()], boss.get_beams()):
                    # Xwingがボスに衝突した場合、爆発エフェクトを追加
                    destroyed_effects.add_effect(star_blaster.get_rect(), screen)
                    print("Xwingがボスに衝突しました！爆発エフェクトを表示")
                    game_state = "GAME_OVER"
                
                # ボスへのビーム衝突判定
                boss_rect = boss.get_rect()
                for beam_rect in beam_rect:
                    if beam_rect.colliderect(boss_rect):
                        pg.mixer.Sound("musics/explosion.ogg").play()
                        # ボスにダメージを与える
                        if boss.take_damage():
                            # ボス撃破時に爆発エフェクトを追加
                                # ボスを消す
                            boss.is_alive = False  # 画面から消える
                            boss.beams.clear()     # ボスのビームも消す

                            for i in range(50):
                                effect_rect = boss.get_rect().copy()  # Rectをコピー
                                effect_rect.x += random.randint(-50, 50)  # X方向をランダムにずらす
                                effect_rect.y += random.randint(-50, 50)  # Y方向をランダムにずらす
                                destroyed_effects.add_effect(effect_rect, screen)
                                destroyed_effects.update_and_draw()
                                pg.display.update()
                                pg.time.delay(200)  # 0.1秒ごとに爆発を順に表示

                            time.sleep(5)
                            game_state = "CLEAR"
                        
                        # 衝突したビームを削除
                        xwing_beam.rects = [beam for beam in xwing_beam.rects 
                                           if not beam.colliderect(boss_rect)]
            else:
                # スコアがENEMY_STOP_SCORE未満の場合はボスを非表示
                if boss.is_alive:
                    print(f"スコア{ENEMY_STOP_SCORE}未満のため、ボスを非表示にします")
                    boss.is_alive = False
        
        elif game_state == "GAME_OVER":
            # GameOver画面を3秒間表示してから自動でスタート画面に戻る
            if use_background and background:
                screen.blit(background, (0, 0))
            else:
                screen.fill(pg.Color("white"))
            
            # 爆発エフェクトの更新・描画（GameOver時も表示）
            destroyed_effects.update_and_draw()
            
            show_game_over(screen)
            
            # 3秒後に自動でスタート画面に戻る
            if frame_counter > 450:  # 60FPS × 3秒 = 180フレーム
                print("GameOverから自動でスタート画面に戻ります")
                game_state = "START"
                # ゲーム状態をリセット
                star_blaster.is_alive = True
                star_blaster.rect.x = 400
                star_blaster.rect.y = 650
                enemy.rects.clear()
                enemy.enemy_beams.clear()
                xwing_beam.rects.clear()
                xwing_beam.reset_score()  # スコアを0にリセット
                destroyed_effects.effects.clear()
                boss.is_alive = False  # スコア0なのでボスは非表示
                boss.hp = BOSS01_HP
                boss.rect.x = 400
                boss.rect.y = 100
                boss.beams.clear()
                frame_counter = 0
                playing_bgm_flg = False
                start_bgm_flg = False    
                fighting_boss = False
            
        elif game_state == "CLEAR":

        # クリア画面の表示
            if use_background and background:
                screen.blit(background, (0, 0))
            else:
                screen.fill(pg.Color("white"))

            show_clear_screen(screen, "You Killed all Evil Eyes!")
    
        pg.display.update()
        pg.time.Clock().tick(60)

        frame_counter += 1


        for event in pg.event.get ():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_SPACE and game_state == "START":
                    # スペースキーでゲーム開始
                    print("ゲーム開始！")
                    time.sleep(2)
                    game_state = "PLAYING"
                    
                elif event.key == pg.K_r and game_state == "CLEAR":
                    # Rキーでクリア画面からリスタート
                    print("ゲームをリスタートします")
                    game_state = "START"
                    star_blaster.is_alive = True
                    star_blaster.rect.x = 400
                    star_blaster.rect.y = 650
                    # 敵とビームをリセット
                    enemy.rects.clear()
                    enemy.enemy_beams.clear()
                    xwing_beam.rects.clear()
                    xwing_beam.reset_score()  # スコアを0にリセット
                    destroyed_effects.effects.clear()
                    
                    # ボスをリセット
                    boss.is_alive = False  # スコア0なのでボスは非表示
                    boss.hp = BOSS01_HP
                    boss.rect.x = 400
                    boss.rect.y = 100
                    boss.beams.clear()
                    
                    playing_bgm_flg = False
                    start_bgm_flg = False    
                    fighting_boss = False
    
asyncio.run(main())
