import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Streamlit 3D 탱크 시뮬레이션", layout="wide")

st.title("🚜 3D 탱크 대전 시뮬레이터 (홈 화면 지원)")
st.caption("메인 홈 화면에서 기종을 선택한 후 출격 버튼을 누르거나 ESC 키를 이용해 메인 메뉴로 돌아갈 수 있습니다.")

col1, col2 = st.columns(2)
with col1:
    st.markdown("""
    **[시스템 조작]**
    * **ESC**: 일시정지 / 메인 메뉴 전환 ⏸️
    * **J / H**: 엔진 시작 / 정지
    * **1 / 2 / 3**: 기종 선택 (6륜 경전차 / 중형 / 중전차)
    """)
with col2:
    st.markdown("""
    **[전투 조종]**
    * **W / A / S / D**: 이동 및 차체 회전
    * **마우스 이동**: 포탑 조준 | **좌클릭 / F**: 포탄 발사 🔥
    * **R**: 1/3인칭 시점 전환 (게임 오버 시 재출격)
    """)

html_code = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { margin: 0; overflow: hidden; background-color: #0b0d10; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; cursor: default; }
        #canvas-container { width: 100vw; height: 100vh; position: relative; }
        
        /* 홈 화면 스스타일 */
        #home-screen {
            position: absolute;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(10, 14, 20, 0.92);
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            z-index: 100;
            backdrop-filter: blur(8px);
        }
        .title {
            font-size: 52px;
            font-weight: 900;
            color: #00ff66;
            text-shadow: 0 0 20px rgba(0, 255, 102, 0.6);
            letter-spacing: 3px;
            margin-bottom: 10px;
        }
        .subtitle {
            font-size: 18px;
            color: #aaa;
            margin-bottom: 40px;
        }
        .select-title {
            font-size: 20px;
            color: #fff;
            margin-bottom: 15px;
            font-weight: bold;
        }
        .tank-option-group {
            display: flex;
            gap: 20px;
            margin-bottom: 40px;
        }
        .tank-card {
            background: rgba(255,255,255,0.05);
            border: 2px solid #333;
            border-radius: 12px;
            padding: 20px 25px;
            width: 180px;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .tank-card:hover {
            border-color: #00ff66;
            transform: translateY(-5px);
            background: rgba(0, 255, 102, 0.1);
        }
        .tank-card.selected {
            border-color: #00ff66;
            background: rgba(0, 255, 102, 0.2);
            box-shadow: 0 0 15px rgba(0, 255, 102, 0.4);
        }
        .tank-card h3 { margin: 0 0 10px 0; color: #fff; font-size: 18px; }
        .tank-card p { margin: 4px 0; color: #bbb; font-size: 13px; }

        .btn-start {
            background: #00aa44;
            color: #fff;
            font-size: 24px;
            font-weight: bold;
            padding: 16px 50px;
            border: 2px solid #00ff66;
            border-radius: 30px;
            cursor: pointer;
            box-shadow: 0 0 20px rgba(0,255,100,0.4);
            transition: 0.2s;
        }
        .btn-start:hover {
            background: #00ff66;
            color: #000;
            box-shadow: 0 0 30px rgba(0,255,102,0.8);
            transform: scale(1.05);
        }

        /* 게임 일시정지 메뉴 */
        #pause-screen {
            display: none;
            position: absolute;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.85);
            flex-direction: column;
            justify-content: center;
            align-items: center;
            z-index: 90;
        }
        .pause-title { font-size: 40px; color: #fff; margin-bottom: 30px; }
        .pause-btn {
            background: #222; color: #fff; border: 1px solid #555;
            padding: 12px 30px; margin: 8px; font-size: 18px; font-weight: bold;
            border-radius: 8px; cursor: pointer; transition: 0.2s;
        }
        .pause-btn:hover { background: #00ff66; color: #000; border-color: #00ff66; }

        /* HUD */
        #hud {
            position: absolute;
            top: 20px; left: 20px;
            color: #00ff00; font-size: 15px; font-weight: bold;
            background: rgba(10, 15, 10, 0.88);
            padding: 18px 22px; border-radius: 8px;
            border: 1px solid #00ff00; line-height: 1.6; min-width: 250px;
            pointer-events: none; user-select: none;
            box-shadow: 0 0 15px rgba(0,255,0,0.2);
            display: none;
        }
        .hp-bar-container { width: 100%; background-color: #333; height: 16px; border-radius: 4px; overflow: hidden; margin-top: 4px; border: 1px solid #666; }
        .hp-bar-fill { height: 100%; background-color: #00ff00; width: 100%; transition: width 0.2s; }
        #heal-msg { display: none; color: #00ff88; font-size: 15px; font-weight: bold; margin-top: 5px; }

        #game-over {
            display: none; position: absolute; top: 50%; left: 50%;
            transform: translate(-50%, -50%); color: #ff3333; font-size: 48px; font-weight: bold;
            background: rgba(0, 0, 0, 0.92); padding: 30px 50px; border: 3px solid #ff3333;
            border-radius: 12px; text-align: center; pointer-events: none; user-select: none;
            box-shadow: 0 0 25px rgba(255, 0, 0, 0.5); z-index: 80;
        }
        .ready { color: #00ff00; }
        .cooldown { color: #ff9900; }
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
</head>
<body>
    <div id="canvas-container">
        <!-- 메인 홈 화면 -->
        <div id="home-screen">
            <div class="title">BATTLE TANK 3D</div>
            <div class="subtitle">시뮬레이션 전장에 출격할 탱크를 선택하세요</div>

            <div class="select-title">출격 장비 선택</div>
            <div class="tank-option-group">
                <div class="tank-card selected" id="card-LIGHT" onclick="homeSelectTank('LIGHT')">
                    <h3>⚡ 6륜 경전차</h3>
                    <p>기동력: 최상</p>
                    <p>특징: 6개 바퀴</p>
                    <p>DMG: 20</p>
                </div>
                <div class="tank-card" id="card-MEDIUM" onclick="homeSelectTank('MEDIUM')">
                    <h3>🛡️ 중형전차</h3>
                    <p>기동력: 보통</p>
                    <p>특징: 밸런스</p>
                    <p>DMG: 30</p>
                </div>
                <div class="tank-card" id="card-HEAVY" onclick="homeSelectTank('HEAVY')">
                    <h3>🐘 중전차</h3>
                    <p>기동력: 느림</p>
                    <p>특징: 원샷 원킬</p>
                    <p>DMG: 100</p>
                </div>
            </div>

            <button class="btn-start" onclick="startGame()">전장 출격 (START)</button>
        </div>

        <!-- 일시정지 메뉴 -->
        <div id="pause-screen">
            <div class="pause-title">PAUSED</div>
            <button class="pause-btn" onclick="resumeGame()">전투 재개 (Resume)</button>
            <button class="pause-btn" onclick="returnToHome()">메인 메뉴로 (Home)</button>
        </div>

        <!-- 게임 내 HUD -->
        <div id="hud">
            <div>기종: <span id="tank-type-name" style="color: #ffff00;">6륜 경전차</span></div>
            <div>주포 데미지: <span id="tank-damage" style="color: #ff3300;">20</span></div>
            <div>내구도: <span id="hp-text">70 / 70</span>
                <div class="hp-bar-container">
                    <div id="hp-bar" class="hp-bar-fill"></div>
                </div>
                <div id="heal-msg">💚 HP +30 수리완료!</div>
            </div>
            <div style="margin-top: 8px;">동력계: <span id="engine-status" style="color: #ff3333;">정지 [J: 시동]</span></div>
            <div>주포 상태: <span id="cooldown-status" class="ready">발사 준비 완료</span></div>
            <div>포구 각도: <span id="elevation-angle" style="color: #00ffff;">0.0°</span></div>
            <div>시점: <span id="camera-status" style="color: #00ffff;">3인칭 [R]</span></div>
            <div>격파 수: <span id="score-status" style="color: #ffff00;">0</span></div>
        </div>

        <div id="game-over">
            MISSION FAILED<br>
            <span style="font-size: 20px; color: #fff;">[R]키를 눌러 재출격하세요</span>
        </div>
    </div>

    <script>
        const TANK_TYPES = {
            LIGHT: { name: "6륜 경전차", maxHp: 70, speed: 0.45, turnSpeed: 0.07, damage: 20, cooldown: 3.5, color: 0x4a6b43, scale: 0.8, isWheeled: true },
            MEDIUM: { name: "중형전차", maxHp: 100, speed: 0.30, turnSpeed: 0.05, damage: 30, cooldown: 5.5, color: 0x2e4f25, scale: 1.0, isWheeled: false },
            HEAVY: { name: "중전차", maxHp: 160, speed: 0.18, turnSpeed: 0.035, damage: 100, cooldown: 7.5, color: 0x1b3316, scale: 1.25, isWheeled: false }
        };

        let currentTypeKey = 'LIGHT';
        let currentType = TANK_TYPES[currentTypeKey];
        let isGameStarted = false;
        let isPaused = false;

        const container = document.getElementById('canvas-container');
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x11161a);
        scene.fog = new THREE.FogExp2(0x11161a, 0.008);

        const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        container.appendChild(renderer.domElement);

        const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
        scene.add(ambientLight);

        const dirLight = new THREE.DirectionalLight(0xfff5ea, 1.0);
        dirLight.position.set(30, 50, 20);
        dirLight.castShadow = true;
        scene.add(dirLight);

        const gridHelper = new THREE.GridHelper(200, 50, 0x00ff00, 0x333333);
        gridHelper.position.y = -0.01;
        scene.add(gridHelper);

        const plane = new THREE.Mesh(
            new THREE.PlaneGeometry(250, 250),
            new THREE.MeshStandardMaterial({ color: 0x1d2124, roughness: 0.8 })
        );
        plane.rotation.x = -Math.PI / 2;
        plane.receiveShadow = true;
        scene.add(plane);

        let playerHp = currentType.maxHp;
        let isGameOver = false;

        function createTankMesh(typeConfig, isAI = false) {
            const group = new THREE.Group();
            const darkMat = new THREE.MeshStandardMaterial({ color: 0x1a1a1a, roughness: 0.9 });
            const wheelMat = new THREE.MeshStandardMaterial({ color: 0x111111, roughness: 0.6, metalness: 0.4 });
            const bodyMat = new THREE.MeshStandardMaterial({ color: typeConfig.color, roughness: 0.5, metalness: 0.3 });
            const detailMat = new THREE.MeshStandardMaterial({ color: 0x222222, metalness: 0.8 });
            const lightMat = new THREE.MeshBasicMaterial({ color: isAI ? 0xff0000 : 0x00ffff });

            const body = new THREE.Mesh(new THREE.BoxGeometry(3, 1.1, 4.2), bodyMat);
            body.position.y = 0.9;
            body.castShadow = true;
            group.add(body);

            if (typeConfig.isWheeled) {
                const wheelPositionsZ = [-1.5, 0, 1.5];
                [-1.65, 1.65].forEach(x => {
                    wheelPositionsZ.forEach(z => {
                        const wheel = new THREE.Mesh(new THREE.CylinderGeometry(0.52, 0.52, 0.5, 16), wheelMat);
                        wheel.rotation.z = Math.PI / 2;
                        wheel.position.set(x, 0.52, z);
                        wheel.castShadow = true;
                        group.add(wheel);
                    });
                });
            } else {
                [-1.6, 1.6].forEach(x => {
                    const track = new THREE.Mesh(new THREE.BoxGeometry(0.6, 0.9, 4.6), darkMat);
                    track.position.set(x, 0.5, 0);
                    group.add(track);
                });
            }

            const turretGroup = new THREE.Group();
            turretGroup.position.set(0, 1.65, 0.1);
            const turret = new THREE.Mesh(new THREE.BoxGeometry(2.2, 0.75, 2.4), bodyMat);
            turret.position.set(0, 0, -0.2);
            turretGroup.add(turret);

            const cannonPitchGroup = new THREE.Group();
            cannonPitchGroup.position.set(0, 0, 0.8);
            const cannon = new THREE.Mesh(new THREE.CylinderGeometry(0.14, 0.16, 2.8, 16), detailMat);
            cannon.rotation.x = Math.PI / 2;
            cannon.position.set(0, 0, 1.2);
            cannonPitchGroup.add(cannon);

            turretGroup.add(cannonPitchGroup);
            group.add(turretGroup);

            return { mesh: group, turretGroup, cannonPitchGroup };
        }

        let playerTankData = createTankMesh(currentType, false);
        let playerTank = playerTankData.mesh;
        let turretGroup = playerTankData.turretGroup;
        let cannonPitchGroup = playerTankData.cannonPitchGroup;
        scene.add(playerTank);

        function rebuildPlayerTank() {
            scene.remove(playerTank);
            playerTankData = createTankMesh(currentType, false);
            playerTank = playerTankData.mesh;
            turretGroup = playerTankData.turretGroup;
            cannonPitchGroup = playerTankData.cannonPitchGroup;
            scene.add(playerTank);
            playerTank.scale.set(currentType.scale, currentType.scale, currentType.scale);
        }

        window.homeSelectTank = function(typeKey) {
            currentTypeKey = typeKey;
            currentType = TANK_TYPES[currentTypeKey];
            document.querySelectorAll('.tank-card').forEach(c => c.classList.remove('selected'));
            document.getElementById(`card-${typeKey}`).classList.add('selected');
        }

        window.startGame = function() {
            document.getElementById('home-screen').style.display = 'none';
            document.getElementById('hud').style.display = 'block';
            document.body.style.cursor = 'crosshair';
            isGameStarted = true;
            rebuildPlayerTank();
            restartGame();
        }

        window.resumeGame = function() {
            isPaused = false;
            document.getElementById('pause-screen').style.display = 'none';
            document.body.style.cursor = 'crosshair';
        }

        window.returnToHome = function() {
            isPaused = false;
            isGameStarted = false;
            document.getElementById('pause-screen').style.display = 'none';
            document.getElementById('hud').style.display = 'none';
            document.getElementById('home-screen').style.display = 'flex';
            document.body.style.cursor = 'default';
        }

        const aiTanks = [];
        function createAITank() {
            const aiData = createTankMesh(TANK_TYPES.MEDIUM, true);
            const aiMesh = aiData.mesh;
            const angle = Math.random() * Math.PI * 2;
            const distance = 30 + Math.random() * 30;
            aiMesh.position.set(Math.sin(angle) * distance, 0, Math.cos(angle) * distance);
            scene.add(aiMesh);
            return { mesh: aiMesh, turretGroup: aiData.turretGroup, cannonPitchGroup: aiData.cannonPitchGroup, hp: 60, lastShootTime: 0, shootCooldown: 4 };
        }

        const bullets = [];
        const bulletGeo = new THREE.SphereGeometry(0.22, 8, 8);
        const heavyBulletGeo = new THREE.SphereGeometry(0.38, 12, 12);
        const playerBulletMat = new THREE.MeshBasicMaterial({ color: 0xffcc00 });
        const aiBulletMat = new THREE.MeshBasicMaterial({ color: 0xff3300 });

        let isEngineOn = false;
        let isFirstPerson = false;
        let killCount = 0;
        const keys = {};
        let lastShootTime = -10.0;

        const raycaster = new THREE.Raycaster();
        const mouse = new THREE.Vector2();
        const targetWorldPoint = new THREE.Vector3();

        function restartGame() {
            playerHp = currentType.maxHp;
            isGameOver = false;
            killCount = 0;
            playerTank.position.set(0, 0, 0);
            playerTank.rotation.set(0, 0, 0);
            document.getElementById('game-over').style.display = "none";
            aiTanks.forEach(ai => scene.remove(ai.mesh));
            aiTanks.length = 0;
            for (let i = 0; i < 2; i++) aiTanks.push(createAITank());
        }

        function triggerFire() {
            if (!isGameStarted || isPaused || isGameOver || !isEngineOn) return;
            const now = performance.now() / 1000;
            if (now - lastShootTime >= currentType.cooldown) {
                lastShootTime = now;
                fireBullet(cannonPitchGroup, true, currentType.damage);
            }
        }

        function fireBullet(pitchGroupRef, isPlayer, damage) {
            const isHeavy = isPlayer && currentTypeKey === 'HEAVY';
            const bullet = new THREE.Mesh(isHeavy ? heavyBulletGeo : bulletGeo, isPlayer ? playerBulletMat : aiBulletMat);
            const muzzleOffset = new THREE.Vector3(0, 0, 2.8 * (isPlayer ? currentType.scale : 1.0));
            muzzleOffset.applyMatrix4(pitchGroupRef.matrixWorld);
            bullet.position.copy(muzzleOffset);

            const direction = new THREE.Vector3(0, 0, 1);
            direction.applyQuaternion(pitchGroupRef.getWorldQuaternion(new THREE.Quaternion())).normalize();

            bullets.push({ mesh: bullet, direction: direction, isPlayer: isPlayer, damage: damage, life: 250 });
            scene.add(bullet);
        }

        window.addEventListener('mousemove', (e) => {
            mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
            mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;
        });

        window.addEventListener('mousedown', (e) => { if (e.button === 0) triggerFire(); });

        window.addEventListener('keydown', (e) => {
            const key = e.key.toLowerCase();
            keys[key] = true;

            if (e.key === 'Escape' && isGameStarted) {
                isPaused = !isPaused;
                document.getElementById('pause-screen').style.display = isPaused ? 'flex' : 'none';
                document.body.style.cursor = isPaused ? 'default' : 'crosshair';
            }

            if (!isGameStarted || isPaused) return;

            if (isGameOver && key === 'r') restartGame();
            if (key === 'j') isEngineOn = true;
            if (key === 'h') isEngineOn = false;
            if (key === 'f') triggerFire();
            if (key === 'r') isFirstPerson = !isFirstPerson;
        });

        window.addEventListener('keyup', (e) => { keys[e.key.toLowerCase()] = false; });

        function animate() {
            requestAnimationFrame(animate);

            if (!isGameStarted || isPaused) {
                // 메인 화면용 카메라 회전 연출
                if (!isGameStarted) {
                    const time = Date.now() * 0.0005;
                    camera.position.x = Math.sin(time) * 12;
                    camera.position.z = Math.cos(time) * 12;
                    camera.position.y = 6;
                    camera.lookAt(0, 1, 0);
                }
                renderer.render(scene, camera);
                return;
            }

            const now = performance.now() / 1000;
            document.getElementById('hp-text').innerText = `${playerHp} / ${currentType.maxHp}`;
            document.getElementById('hp-bar').style.width = `${Math.max(0, playerHp / currentType.maxHp) * 100}%`;
            document.getElementById('engine-status').innerText = isEngineOn ? "가동 중 [ON]" : "정지 [OFF - J입력]";
            document.getElementById('engine-status').style.color = isEngineOn ? "#00ff00" : "#ff3333";
            document.getElementById('score-status').innerText = killCount;

            raycaster.setFromCamera(mouse, camera);
            const intersects = raycaster.intersectObject(plane);
            if (intersects.length > 0) targetWorldPoint.copy(intersects[0].point);

            if (!isGameOver) {
                if (isEngineOn) {
                    if (keys['w']) playerTank.translateZ(currentType.speed);
                    if (keys['s']) playerTank.translateZ(-currentType.speed);
                    if (keys['a']) playerTank.rotation.y += currentType.turnSpeed;
                    if (keys['d']) playerTank.rotation.y -= currentType.turnSpeed;
                }

                const localTarget = targetWorldPoint.clone();
                playerTank.worldToLocal(localTarget);
                turretGroup.rotation.y = Math.atan2(localTarget.x, localTarget.z);

                aiTanks.forEach(ai => {
                    ai.mesh.lookAt(playerTank.position.x, ai.mesh.position.y, playerTank.position.z);
                    if (ai.mesh.position.distanceTo(playerTank.position) > 16) ai.mesh.translateZ(0.16);
                    if (now - ai.lastShootTime >= ai.shootCooldown) {
                        ai.lastShootTime = now;
                        fireBullet(ai.cannonPitchGroup, false, 18);
                    }
                });
            }

            for (let i = bullets.length - 1; i >= 0; i--) {
                const b = bullets[i];
                b.mesh.position.addScaledVector(b.direction, 0.7);
                b.life -= 1;

                if (!isGameOver) {
                    if (b.isPlayer) {
                        aiTanks.forEach((ai, j) => {
                            if (b.mesh.position.distanceTo(ai.mesh.position) < 2.6) {
                                ai.hp -= b.damage;
                                scene.remove(b.mesh);
                                bullets.splice(i, 1);
                                if (ai.hp <= 0) {
                                    scene.remove(ai.mesh);
                                    aiTanks.splice(j, 1);
                                    killCount++;
                                    setTimeout(() => aiTanks.push(createAITank()), 2000);
                                }
                            }
                        });
                    } else if (b.mesh.position.distanceTo(playerTank.position) < 2.6) {
                        playerHp -= b.damage;
                        scene.remove(b.mesh);
                        bullets.splice(i, 1);
                        if (playerHp <= 0) {
                            playerHp = 0;
                            isGameOver = true;
                            document.getElementById('game-over').style.display = "block";
                        }
                    }
                }

                if (b.life <= 0) {
                    scene.remove(b.mesh);
                    bullets.splice(i, 1);
                }
            }

            if (isFirstPerson) {
                const fpOffset = new THREE.Vector3(0, 0.4 * currentType.scale, 0.4 * currentType.scale).applyMatrix4(cannonPitchGroup.matrixWorld);
                camera.position.copy(fpOffset);
                camera.lookAt(new THREE.Vector3(0, 0.4 * currentType.scale, 20).applyMatrix4(cannonPitchGroup.matrixWorld));
            } else {
                const tpOffset = new THREE.Vector3(0, 6.5 * currentType.scale, -13 * currentType.scale).applyMatrix4(playerTank.matrixWorld);
                camera.position.copy(tpOffset);
                camera.lookAt(playerTank.position.x, playerTank.position.y + 1, playerTank.position.z);
            }

            renderer.render(scene, camera);
        }

        animate();
    </script>
</body>
</html>
"""

components.html(html_code, height=750)
