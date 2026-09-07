import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Streamlit 3D 탱크 시뮬레이션", layout="wide")

st.title("🚜 3D 탱크 시뮬레이터 (마우스 포탑 조종)")
st.caption("Streamlit + Three.js를 활용한 대전 시뮬레이션 - 마우스로 목표를 겨냥하세요!")

# 조작 키 안내
col1, col2 = st.columns(2)
with col1:
    st.markdown("""
    **[엔진 조작]**
    * **J**: 엔진 시작
    * **H**: 엔진 정지
    """)
with col2:
    st.markdown("""
    **[탱크 조종 & 조작]** (엔진 ON 상태)
    * **W**: 전진 | **S**: 후진
    * **A**: 차체 좌회전 | **D**: 차체 우회전
    * **마우스 이동**: 포탑/포신 조준 🎯
    * **F** 또는 **마우스 왼쪽 클릭**: 포탄 발사 🔥 (쿨타임 6초)
    * **R**: 시점 전환 🎥 (1인칭 ↔ 3인칭)
    """)

# 3D 캔버스 및 Three.js 게임 로직 HTML/JS
html_code = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { margin: 0; overflow: hidden; background-color: #1a1a1a; font-family: sans-serif; cursor: crosshair; }
        #canvas-container { width: 100vw; height: 100vh; position: relative; }
        #hud {
            position: absolute;
            top: 20px;
            left: 20px;
            color: #00ff00;
            font-size: 18px;
            font-weight: bold;
            background: rgba(0, 0, 0, 0.8);
            padding: 15px 20px;
            border-radius: 8px;
            border: 1px solid #00ff00;
            line-height: 1.6;
            min-width: 220px;
            pointer-events: none;
            user-select: none;
        }
        .hp-bar-container {
            width: 100%;
            background-color: #444;
            height: 16px;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 4px;
            border: 1px solid #fff;
        }
        .hp-bar-fill {
            height: 100%;
            background-color: #00ff00;
            width: 100%;
            transition: width 0.2s ease-in-out;
        }
        #game-over {
            display: none;
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: #ff0000;
            font-size: 48px;
            font-weight: bold;
            background: rgba(0, 0, 0, 0.9);
            padding: 30px 50px;
            border: 3px solid #ff0000;
            border-radius: 12px;
            text-align: center;
            pointer-events: none;
            user-select: none;
        }
        .ready { color: #00ff00; }
        .cooldown { color: #ff9900; }
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
</head>
<body>
    <div id="canvas-container">
        <div id="hud">
            <div>플레이어 HP: <span id="hp-text">100 / 100</span>
                <div class="hp-bar-container">
                    <div id="hp-bar" class="hp-bar-fill"></div>
                </div>
            </div>
            <div style="margin-top: 8px;">엔진 상태: <span id="engine-status" style="color: #ff3333;">OFF (J를 눌러 시작)</span></div>
            <div>포탄 상태: <span id="cooldown-status" class="ready">발사 가능 [F / 클릭]</span></div>
            <div>시점 모드: <span id="camera-status" style="color: #00ffff;">3인칭 [R로 변경]</span></div>
            <div>처치한 적 수: <span id="score-status" style="color: #ffff00;">0</span></div>
        </div>
        <div id="game-over">
            GAME OVER<br>
            <span style="font-size: 20px; color: #fff;">[R]키를 눌러 다시 시작하세요</span>
        </div>
    </div>

    <script>
        const container = document.getElementById('canvas-container');
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x1a1a1a);

        const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.shadowMap.enabled = true;
        container.appendChild(renderer.domElement);

        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        scene.add(ambientLight);

        const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
        dirLight.position.set(20, 40, 20);
        dirLight.castShadow = true;
        scene.add(dirLight);

        const gridHelper = new THREE.GridHelper(200, 50, 0x00ff00, 0x444444);
        gridHelper.position.y = -0.01;
        scene.add(gridHelper);

        const planeGeo = new THREE.PlaneGeometry(200, 200);
        const planeMat = new THREE.MeshStandardMaterial({ color: 0x222222 });
        const plane = new THREE.Mesh(planeGeo, planeMat);
        plane.rotation.x = -Math.PI / 2;
        plane.receiveShadow = true;
        scene.add(plane);

        const MAX_PLAYER_HP = 100;
        let playerHp = MAX_PLAYER_HP;
        let isGameOver = false;

        // --- 플레이어 탱크 구조 ---
        const playerTank = new THREE.Group(); // 차체 + 포탑 포함 그룹

        const bodyGeo = new THREE.BoxGeometry(3, 1.2, 4);
        const bodyMat = new THREE.MeshStandardMaterial({ color: 0x2e5a27 });
        const body = new THREE.Mesh(bodyGeo, bodyMat);
        body.position.y = 0.8;
        body.castShadow = true;
        playerTank.add(body);

        // 독립 회전할 포탑 피봇 그룹
        const turretGroup = new THREE.Group();
        turretGroup.position.set(0, 1.8, 0);

        const turretGeo = new THREE.BoxGeometry(2, 0.8, 2);
        const turretMat = new THREE.MeshStandardMaterial({ color: 0x3d7534 });
        const turret = new THREE.Mesh(turretGeo, turretMat);
        turret.position.set(0, 0, -0.2);
        turret.castShadow = true;
        turretGroup.add(turret);

        const cannonGeo = new THREE.CylinderGeometry(0.15, 0.15, 2.5, 16);
        const cannonMat = new THREE.MeshStandardMaterial({ color: 0x111111 });
        const cannon = new THREE.Mesh(cannonGeo, cannonMat);
        cannon.rotation.x = Math.PI / 2;
        cannon.position.set(0, 0, 1.5);
        cannon.castShadow = true;
        turretGroup.add(cannon);

        playerTank.add(turretGroup);
        scene.add(playerTank);

        // --- AI 탱크 구조 ---
        const aiTanks = [];
        const aiBodyMat = new THREE.MeshStandardMaterial({ color: 0x8b0000 });
        const aiTurretMat = new THREE.MeshStandardMaterial({ color: 0xb22222 });

        function createAITank() {
            const aiTank = new THREE.Group();
            
            const aiBody = new THREE.Mesh(bodyGeo, aiBodyMat);
            aiBody.position.y = 0.8;
            aiBody.castShadow = true;
            aiTank.add(aiBody);

            const aiTurretGroup = new THREE.Group();
            aiTurretGroup.position.set(0, 1.8, 0);

            const aiTurret = new THREE.Mesh(turretGeo, aiTurretMat);
            aiTurret.position.set(0, 0, -0.2);
            aiTurret.castShadow = true;
            aiTurretGroup.add(aiTurret);

            const aiCannon = new THREE.Mesh(cannonGeo, cannonMat);
            aiCannon.rotation.x = Math.PI / 2;
            aiCannon.position.set(0, 0, 1.5);
            aiCannon.castShadow = true;
            aiTurretGroup.add(aiCannon);

            aiTank.add(aiTurretGroup);

            const angle = Math.random() * Math.PI * 2;
            const distance = 30 + Math.random() * 30;
            aiTank.position.set(
                playerTank.position.x + Math.sin(angle) * distance,
                0,
                playerTank.position.z + Math.cos(angle) * distance
            );

            scene.add(aiTank);

            return {
                mesh: aiTank,
                turretGroup: aiTurretGroup,
                hp: 50,
                maxHp: 50,
                lastShootTime: 0,
                shootCooldown: 3.0 + Math.random() * 2
            };
        }

        for (let i = 0; i < 2; i++) {
            aiTanks.push(createAITank());
        }

        const bullets = [];
        const bulletGeo = new THREE.SphereGeometry(0.25, 8, 8);
        const playerBulletMat = new THREE.MeshStandardMaterial({ color: 0xffa500, emissive: 0xff3300 });
        const aiBulletMat = new THREE.MeshStandardMaterial({ color: 0xff0000, emissive: 0xaa0000 });

        let isEngineOn = false;
        let isFirstPerson = false;
        let killCount = 0;
        const keys = {};

        // --- 속도 파라미터 ---
        const speed = 0.30;       // 이동 속도
        const turnSpeed = 0.05;   // 회전 속도
        const bulletSpeed = 0.6;  // 포탄 비행 속도

        const COOLDOWN_TIME = 6.0;
        let lastShootTime = -COOLDOWN_TIME;

        // --- 마우스 추적 레이캐스터 ---
        const raycaster = new THREE.Raycaster();
        const mouse = new THREE.Vector2();
        const targetWorldPoint = new THREE.Vector3();

        const engineStatusEl = document.getElementById('engine-status');
        const cooldownStatusEl = document.getElementById('cooldown-status');
        const cameraStatusEl = document.getElementById('camera-status');
        const scoreStatusEl = document.getElementById('score-status');
        const hpTextEl = document.getElementById('hp-text');
        const hpBarEl = document.getElementById('hp-bar');
        const gameOverEl = document.getElementById('game-over');

        function updateHUD(currentTime) {
            hpTextEl.innerText = `${playerHp} / ${MAX_PLAYER_HP}`;
            const hpRatio = Math.max(0, playerHp / MAX_PLAYER_HP);
            hpBarEl.style.width = `${hpRatio * 100}%`;
            
            if (hpRatio > 0.5) {
                hpBarEl.style.backgroundColor = "#00ff00";
            } else if (hpRatio > 0.25) {
                hpBarEl.style.backgroundColor = "#ffaa00";
            } else {
                hpBarEl.style.backgroundColor = "#ff0000";
            }

            if (isEngineOn) {
                engineStatusEl.innerText = "ON";
                engineStatusEl.style.color = "#00ff00";
            } else {
                engineStatusEl.innerText = "OFF (J를 눌러 시작)";
                engineStatusEl.style.color = "#ff3333";
            }

            const elapsedTime = currentTime - lastShootTime;
            const remainingTime = COOLDOWN_TIME - elapsedTime;

            if (remainingTime <= 0) {
                cooldownStatusEl.innerText = "발사 가능 [F / 클릭]";
                cooldownStatusEl.className = "ready";
            } else {
                cooldownStatusEl.innerText = `재장전 중... (${remainingTime.toFixed(1)}초)`;
                cooldownStatusEl.className = "cooldown";
            }

            if (isFirstPerson) {
                cameraStatusEl.innerText = "1인칭 (조종석)";
                cameraStatusEl.style.color = "#ff00ff";
            } else {
                cameraStatusEl.innerText = "3인칭 (전체 뷰)";
                cameraStatusEl.style.color = "#00ffff";
            }

            scoreStatusEl.innerText = killCount;
        }

        function restartGame() {
            playerHp = MAX_PLAYER_HP;
            isGameOver = false;
            killCount = 0;
            playerTank.position.set(0, 0, 0);
            playerTank.rotation.set(0, 0, 0);
            turretGroup.rotation.set(0, 0, 0);
            gameOverEl.style.display = "none";
            
            aiTanks.forEach(ai => scene.remove(ai.mesh));
            aiTanks.length = 0;
            for (let i = 0; i < 2; i++) {
                aiTanks.push(createAITank());
            }
        }

        function triggerFire() {
            if (isGameOver || !isEngineOn) return;
            const now = performance.now() / 1000;
            if (now - lastShootTime >= COOLDOWN_TIME) {
                lastShootTime = now;
                fireBullet(turretGroup, true);
            }
        }

        function fireBullet(turretRef, isPlayer) {
            const bullet = new THREE.Mesh(bulletGeo, isPlayer ? playerBulletMat : aiBulletMat);
            
            const muzzleOffset = new THREE.Vector3(0, 0, 2.8);
            muzzleOffset.applyMatrix4(turretRef.matrixWorld);
            bullet.position.copy(muzzleOffset);

            const direction = new THREE.Vector3(0, 0, 1);
            direction.applyQuaternion(turretRef.getWorldQuaternion(new THREE.Quaternion())).normalize();

            bullets.push({
                mesh: bullet,
                direction: direction,
                isPlayer: isPlayer,
                life: 300
            });

            scene.add(bullet);
        }

        // --- 이벤트 리스너 ---
        window.addEventListener('mousemove', (e) => {
            mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
            mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;
        });

        window.addEventListener('mousedown', (e) => {
            if (e.button === 0) { // 마우스 좌클릭
                triggerFire();
            }
        });

        window.addEventListener('keydown', (e) => {
            const key = e.key.toLowerCase();
            keys[key] = true;

            if (isGameOver) {
                if (key === 'r') restartGame();
                return;
            }

            if (key === 'j') {
                isEngineOn = true;
            } else if (key === 'h') {
                isEngineOn = false;
            } else if (key === 'f') {
                triggerFire();
            } else if (key === 'r') {
                isFirstPerson = !isFirstPerson;
            }
        });

        window.addEventListener('keyup', (e) => {
            keys[e.key.toLowerCase()] = false;
        });

        function animate() {
            requestAnimationFrame(animate);

            const now = performance.now() / 1000;
            updateHUD(now);

            // --- 마우스 좌표를 3D 공간 상의 바닥 좌표로 변환 ---
            raycaster.setFromCamera(mouse, camera);
            const intersects = raycaster.intersectObject(plane);
            if (intersects.length > 0) {
                targetWorldPoint.copy(intersects[0].point);
            }

            if (!isGameOver) {
                // 탱크 이동
                if (isEngineOn) {
                    if (keys['w']) playerTank.translateZ(speed);
                    if (keys['s']) playerTank.translateZ(-speed);
                    if (keys['a']) playerTank.rotation.y += turnSpeed;
                    if (keys['d']) playerTank.rotation.y -= turnSpeed;
                }

                // 포탑 회전: 마우스 지점을 바라보도록 제어
                const localTarget = targetWorldPoint.clone();
                playerTank.worldToLocal(localTarget);
                const targetAngle = Math.atan2(localTarget.x, localTarget.z);
                turretGroup.rotation.y = targetAngle;

                // AI 탱크 로직
                aiTanks.forEach(ai => {
                    const targetPosition = new THREE.Vector3(playerTank.position.x, ai.mesh.position.y, playerTank.position.z);
                    ai.mesh.lookAt(targetPosition);

                    const dist = ai.mesh.position.distanceTo(playerTank.position);
                    if (dist > 15) {
                        ai.mesh.translateZ(speed * 0.6);
                    }

                    if (now - ai.lastShootTime >= ai.shootCooldown) {
                        ai.lastShootTime = now;
                        fireBullet(ai.turretGroup, false);
                    }
                });
            }

            // 포탄 이동 & 충돌 처리
            for (let i = bullets.length - 1; i >= 0; i--) {
                const b = bullets[i];
                b.mesh.position.addScaledVector(b.direction, bulletSpeed);
                b.life -= 1;

                if (!isGameOver) {
                    if (b.isPlayer) {
                        for (let j = aiTanks.length - 1; j >= 0; j--) {
                            const ai = aiTanks[j];
                            if (b.mesh.position.distanceTo(ai.mesh.position) < 2.5) {
                                ai.hp -= 25;

                                scene.remove(b.mesh);
                                b.mesh.geometry.dispose();
                                bullets.splice(i, 1);

                                if (ai.hp <= 0) {
                                    scene.remove(ai.mesh);
                                    aiTanks.splice(j, 1);
                                    killCount += 1;

                                    setTimeout(() => {
                                        aiTanks.push(createAITank());
                                    }, 2000);
                                }
                                break;
                            }
                        }
                    } else {
                        if (b.mesh.position.distanceTo(playerTank.position) < 2.5) {
                            playerHp -= 25;

                            scene.remove(b.mesh);
                            b.mesh.geometry.dispose();
                            bullets.splice(i, 1);

                            if (playerHp <= 0) {
                                playerHp = 0;
                                isGameOver = true;
                                gameOverEl.style.display = "block";
                            }
                            continue;
                        }
                    }
                }

                if (b.life <= 0) {
                    scene.remove(b.mesh);
                    b.mesh.geometry.dispose();
                    bullets.splice(i, 1);
                }
            }

            // 카메라 시점 업데이트
            if (isFirstPerson) {
                const fpOffset = new THREE.Vector3(0, 2.0, 0.5);
                fpOffset.applyMatrix4(turretGroup.matrixWorld);
                camera.position.copy(fpOffset);

                const lookAtOffset = new THREE.Vector3(0, 2.0, 20);
                lookAtOffset.applyMatrix4(turretGroup.matrixWorld);
                camera.lookAt(lookAtOffset);
            } else {
                const tpOffset = new THREE.Vector3(0, 6, -12);
                const tpPosition = tpOffset.applyMatrix4(playerTank.matrixWorld);
                camera.position.copy(tpPosition);
                camera.lookAt(playerTank.position.x, playerTank.position.y + 1, playerTank.position.z);
            }

            renderer.render(scene, camera);
        }

        window.addEventListener('resize', () => {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        });

        animate();
    </script>
</body>
</html>
"""

components.html(html_code, height=650)
