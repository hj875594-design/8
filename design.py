import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Streamlit 3D 탱크 시뮬레이션", layout="wide")

st.title("🚜 3D 탱크 시뮬레이터 (탱크 종류 선택 가능)")
st.caption("Streamlit + Three.js를 활용한 대전 시뮬레이션 - 탱크 종류를 직접 골라 전투에 참여하세요!")

# 조작 키 안내
col1, col2 = st.columns(2)
with col1:
    st.markdown("""
    **[엔진 조작]**
    * **J**: 엔진 시작
    * **H**: 엔진 정지
    * **1 / 2 / 3**: 게임 중 탱크 변경 (경탱크/중형탱크/중전차)
    """)
with col2:
    st.markdown("""
    **[탱크 조종 & 조작]** (엔진 ON 상태)
    * **W**: 전진 | **S**: 후진
    * **A**: 차체 좌회전 | **D**: 차체 우회전
    * **마우스 이동**: 포탑/포신 조준 🎯
    * **F** 또는 **마우스 왼쪽 클릭**: 포탄 발사 🔥
    * **R**: 시점 전환 🎥 (1인칭 ↔ 3인칭)
    * **🟩 초록 십자가**: 체력 키트 (획득 시 **HP +30** 회복)
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
            font-size: 16px;
            font-weight: bold;
            background: rgba(0, 0, 0, 0.85);
            padding: 15px 20px;
            border-radius: 8px;
            border: 1px solid #00ff00;
            line-height: 1.6;
            min-width: 240px;
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
        #heal-msg {
            display: none;
            color: #00ff88;
            font-size: 15px;
            font-weight: bold;
            margin-top: 5px;
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

        #tank-selector {
            position: absolute;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            gap: 12px;
            background: rgba(0, 0, 0, 0.8);
            padding: 10px 15px;
            border-radius: 10px;
            border: 1px solid #00ff00;
        }
        .tank-btn {
            background: #222;
            color: #fff;
            border: 1px solid #555;
            padding: 8px 14px;
            border-radius: 6px;
            cursor: pointer;
            font-weight: bold;
            transition: 0.2s;
        }
        .tank-btn:hover {
            background: #444;
        }
        .tank-btn.active {
            background: #00aa44;
            border-color: #00ff66;
            color: #fff;
        }
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
</head>
<body>
    <div id="canvas-container">
        <div id="hud">
            <div>선택된 탱크: <span id="tank-type-name" style="color: #ffff00;">중형탱크</span></div>
            <div>플레이어 HP: <span id="hp-text">100 / 100</span>
                <div class="hp-bar-container">
                    <div id="hp-bar" class="hp-bar-fill"></div>
                </div>
                <div id="heal-msg">💚 HP +30 회복!</div>
            </div>
            <div style="margin-top: 8px;">엔진 상태: <span id="engine-status" style="color: #ff3333;">OFF (J를 눌러 시작)</span></div>
            <div>포탄 상태: <span id="cooldown-status" class="ready">발사 가능 [F / 클릭]</span></div>
            <div>시점 모드: <span id="camera-status" style="color: #00ffff;">3인칭 [R로 변경]</span></div>
            <div>처치한 적 수: <span id="score-status" style="color: #ffff00;">0</span></div>
        </div>

        <div id="tank-selector">
            <button class="tank-btn" onclick="selectTankType('LIGHT')">[1] ⚡ 경탱크 (기동성)</button>
            <button class="tank-btn active" onclick="selectTankType('MEDIUM')">[2] 🛡️ 중형탱크 (밸런스)</button>
            <button class="tank-btn" onclick="selectTankType('HEAVY')">[3] 🐘 중전차 (고체력/고화력)</button>
        </div>

        <div id="game-over">
            GAME OVER<br>
            <span style="font-size: 20px; color: #fff;">[R]키를 눌러 다시 시작하세요</span>
        </div>
    </div>

    <script>
        const TANK_TYPES = {
            LIGHT: {
                name: "경탱크",
                maxHp: 70,
                speed: 0.45,
                turnSpeed: 0.07,
                damage: 20,
                cooldown: 4.0,
                color: 0x4a7c59,
                scale: 0.8
            },
            MEDIUM: {
                name: "중형탱크",
                maxHp: 100,
                speed: 0.30,
                turnSpeed: 0.05,
                damage: 25,
                cooldown: 6.0,
                color: 0x2e5a27,
                scale: 1.0
            },
            HEAVY: {
                name: "중전차",
                maxHp: 160,
                speed: 0.18,
                turnSpeed: 0.035,
                damage: 40,
                cooldown: 8.0,
                color: 0x1c3b18,
                scale: 1.25
            }
        };

        let currentTypeKey = 'MEDIUM';
        let currentType = TANK_TYPES[currentTypeKey];

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

        let playerHp = currentType.maxHp;
        let isGameOver = false;

        // --- 플레이어 탱크 ---
        const playerTank = new THREE.Group();
        const playerBodyMat = new THREE.MeshStandardMaterial({ color: currentType.color });
        const playerTurretMat = new THREE.MeshStandardMaterial({ color: currentType.color });

        const bodyGeo = new THREE.BoxGeometry(3, 1.2, 4);
        const body = new THREE.Mesh(bodyGeo, playerBodyMat);
        body.position.y = 0.8;
        body.castShadow = true;
        playerTank.add(body);

        const turretGroup = new THREE.Group();
        turretGroup.position.set(0, 1.8, 0);

        const turretGeo = new THREE.BoxGeometry(2, 0.8, 2);
        const turret = new THREE.Mesh(turretGeo, playerTurretMat);
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

        function applyTankStats() {
            currentType = TANK_TYPES[currentTypeKey];
            playerTank.scale.set(currentType.scale, currentType.scale, currentType.scale);
            playerBodyMat.color.setHex(currentType.color);
            playerTurretMat.color.setHex(currentType.color);
            document.getElementById('tank-type-name').innerText = currentType.name;

            // 스위치 버튼 스타일 활성화
            const buttons = document.querySelectorAll('.tank-btn');
            buttons.forEach(btn => btn.classList.remove('active'));
            if (currentTypeKey === 'LIGHT') buttons[0].classList.add('active');
            if (currentTypeKey === 'MEDIUM') buttons[1].classList.add('active');
            if (currentTypeKey === 'HEAVY') buttons[2].classList.add('active');
        }

        window.selectTankType = function(typeKey) {
            currentTypeKey = typeKey;
            applyTankStats();
            playerHp = Math.min(playerHp, currentType.maxHp);
        };

        // --- AI 탱크 ---
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
                shootCooldown: 3.5 + Math.random() * 2
            };
        }

        for (let i = 0; i < 2; i++) {
            aiTanks.push(createAITank());
        }

        // --- 체력 아이템 ---
        const healthPacks = [];
        const packMat = new THREE.MeshStandardMaterial({ color: 0x00ff66, emissive: 0x00aa33 });
        const packBaseGeo = new THREE.BoxGeometry(0.5, 1.5, 0.5);
        const packCrossGeo = new THREE.BoxGeometry(1.5, 0.5, 0.5);

        function createHealthPack() {
            const packGroup = new THREE.Group();
            const vMesh = new THREE.Mesh(packBaseGeo, packMat);
            const hMesh = new THREE.Mesh(packCrossGeo, packMat);
            packGroup.add(vMesh);
            packGroup.add(hMesh);

            const angle = Math.random() * Math.PI * 2;
            const distance = 15 + Math.random() * 25;
            packGroup.position.set(
                playerTank.position.x + Math.sin(angle) * distance,
                1.5,
                playerTank.position.z + Math.cos(angle) * distance
            );

            scene.add(packGroup);
            return packGroup;
        }

        for (let i = 0; i < 2; i++) {
            healthPacks.push(createHealthPack());
        }

        const bullets = [];
        const bulletGeo = new THREE.SphereGeometry(0.25, 8, 8);
        const playerBulletMat = new THREE.MeshStandardMaterial({ color: 0xffa500, emissive: 0xff3300 });
        const aiBulletMat = new THREE.MeshStandardMaterial({ color: 0xff0000, emissive: 0xaa0000 });

        let isEngineOn = false;
        let isFirstPerson = false;
        let killCount = 0;
        const keys = {};

        let lastShootTime = -10.0;
        let lastPackSpawnTime = 0;

        const raycaster = new THREE.Raycaster();
        const mouse = new THREE.Vector2();
        const targetWorldPoint = new THREE.Vector3();

        const engineStatusEl = document.getElementById('engine-status');
        const cooldownStatusEl = document.getElementById('cooldown-status');
        const cameraStatusEl = document.getElementById('camera-status');
        const scoreStatusEl = document.getElementById('score-status');
        const hpTextEl = document.getElementById('hp-text');
        const hpBarEl = document.getElementById('hp-bar');
        const healMsgEl = document.getElementById('heal-msg');
        const gameOverEl = document.getElementById('game-over');

        function showHealMessage() {
            healMsgEl.style.display = "block";
            setTimeout(() => {
                healMsgEl.style.display = "none";
            }, 1200);
        }

        function updateHUD(currentTime) {
            hpTextEl.innerText = `${playerHp} / ${currentType.maxHp}`;
            const hpRatio = Math.max(0, playerHp / currentType.maxHp);
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
            const remainingTime = currentType.cooldown - elapsedTime;

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
            playerHp = currentType.maxHp;
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

            healthPacks.forEach(pack => scene.remove(pack));
            healthPacks.length = 0;
            for (let i = 0; i < 2; i++) {
                healthPacks.push(createHealthPack());
            }
        }

        function triggerFire() {
            if (isGameOver || !isEngineOn) return;
            const now = performance.now() / 1000;
            if (now - lastShootTime >= currentType.cooldown) {
                lastShootTime = now;
                fireBullet(turretGroup, true, currentType.damage);
            }
        }

        function fireBullet(turretRef, isPlayer, damage) {
            const bullet = new THREE.Mesh(bulletGeo, isPlayer ? playerBulletMat : aiBulletMat);
            
            const muzzleOffset = new THREE.Vector3(0, 0, 2.8 * currentType.scale);
            muzzleOffset.applyMatrix4(turretRef.matrixWorld);
            bullet.position.copy(muzzleOffset);

            const direction = new THREE.Vector3(0, 0, 1);
            direction.applyQuaternion(turretRef.getWorldQuaternion(new THREE.Quaternion())).normalize();

            bullets.push({
                mesh: bullet,
                direction: direction,
                isPlayer: isPlayer,
                damage: damage,
                life: 300
            });

            scene.add(bullet);
        }

        window.addEventListener('mousemove', (e) => {
            mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
            mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;
        });

        window.addEventListener('mousedown', (e) => {
            if (e.button === 0) {
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

            if (key === '1') selectTankType('LIGHT');
            else if (key === '2') selectTankType('MEDIUM');
            else if (key === '3') selectTankType('HEAVY');
            else if (key === 'j') isEngineOn = true;
            else if (key === 'h') isEngineOn = false;
            else if (key === 'f') triggerFire();
            else if (key === 'r') isFirstPerson = !isFirstPerson;
        });

        window.addEventListener('keyup', (e) => {
            keys[e.key.toLowerCase()] = false;
        });

        function animate() {
            requestAnimationFrame(animate);

            const now = performance.now() / 1000;
            updateHUD(now);

            raycaster.setFromCamera(mouse, camera);
            const intersects = raycaster.intersectObject(plane);
            if (intersects.length > 0) {
                targetWorldPoint.copy(intersects[0].point);
            }

            if (!isGameOver) {
                // 플레이어 탱크 이동
                if (isEngineOn) {
                    if (keys['w']) playerTank.translateZ(currentType.speed);
                    if (keys['s']) playerTank.translateZ(-currentType.speed);
                    if (keys['a']) playerTank.rotation.y += currentType.turnSpeed;
                    if (keys['d']) playerTank.rotation.y -= currentType.turnSpeed;
                }

                // 포탑 조준
                const localTarget = targetWorldPoint.clone();
                playerTank.worldToLocal(localTarget);
                const targetAngle = Math.atan2(localTarget.x, localTarget.z);
                turretGroup.rotation.y = targetAngle;

                // 아이템 획득
                for (let i = healthPacks.length - 1; i >= 0; i--) {
                    const pack = healthPacks[i];
                    pack.rotation.y += 0.03;

                    if (playerTank.position.distanceTo(pack.position) < 3.0) {
                        if (playerHp < currentType.maxHp) {
                            playerHp = Math.min(currentType.maxHp, playerHp + 30);
                            showHealMessage();

                            scene.remove(pack);
                            healthPacks.splice(i, 1);
                        }
                    }
                }

                if (now - lastPackSpawnTime > 10.0 && healthPacks.length < 3) {
                    lastPackSpawnTime = now;
                    healthPacks.push(createHealthPack());
                }

                // AI 탱크
                aiTanks.forEach(ai => {
                    const targetPosition = new THREE.Vector3(playerTank.position.x, ai.mesh.position.y, playerTank.position.z);
                    ai.mesh.lookAt(targetPosition);

                    const dist = ai.mesh.position.distanceTo(playerTank.position);
                    if (dist > 15) {
                        ai.mesh.translateZ(0.18);
                    }

                    if (now - ai.lastShootTime >= ai.shootCooldown) {
                        ai.lastShootTime = now;
                        fireBullet(ai.turretGroup, false, 20);
                    }
                });
            }

            // 포탄 이동 및 충돌
            for (let i = bullets.length - 1; i >= 0; i--) {
                const b = bullets[i];
                b.mesh.position.addScaledVector(b.direction, 0.6);
                b.life -= 1;

                if (!isGameOver) {
                    if (b.isPlayer) {
                        for (let j = aiTanks.length - 1; j >= 0; j--) {
                            const ai = aiTanks[j];
                            if (b.mesh.position.distanceTo(ai.mesh.position) < 2.5) {
                                ai.hp -= b.damage;

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
                        if (b.mesh.position.distanceTo(playerTank.position) < 2.5 * currentType.scale) {
                            playerHp -= b.damage;

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

            // 카메라 위치 설정
            if (isFirstPerson) {
                const fpOffset = new THREE.Vector3(0, 2.0 * currentType.scale, 0.5 * currentType.scale);
                fpOffset.applyMatrix4(turretGroup.matrixWorld);
                camera.position.copy(fpOffset);

                const lookAtOffset = new THREE.Vector3(0, 2.0 * currentType.scale, 20);
                lookAtOffset.applyMatrix4(turretGroup.matrixWorld);
                camera.lookAt(lookAtOffset);
            } else {
                const tpOffset = new THREE.Vector3(0, 6 * currentType.scale, -12 * currentType.scale);
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

        applyTankStats();
        animate();
    </script>
</body>
</html>
"""

components.html(html_code, height=680)
