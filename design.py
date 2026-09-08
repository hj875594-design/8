import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Streamlit High-Detail 3D 탱크 시뮬레이션", layout="wide")

st.title("🚜 3D 탱크 대전 시뮬레이터 (6륜 경전차 추가 버전)")
st.caption("경전차(LIGHT) 선택 시 총 6개의 바퀴가 달린 민첩한 6륜 경전차로 출격합니다!")

# 조작 키 안내
col1, col2 = st.columns(2)
with col1:
    st.markdown("""
    **[엔진 조작]**
    * **J**: 엔진 시작
    * **H**: 엔진 정지
    * **1 / 2 / 3**: 탱크 변경 (**1번: 6륜 경전차 ⚡**)
    """)
with col2:
    st.markdown("""
    **[탱크 조종]** (엔진 ON 상태)
    * **W**: 전진 | **S**: 후진
    * **A / D**: 차체 좌/우 회전
    * **마우스**: 포탑 좌우 회전 및 **포구 위/아래 조준** 🎯
    * **F** 또는 **마우스 좌클릭**: 포탄 발사 🔥
    * **R**: 1인칭 / 3인칭 시점 전환
    """)

html_code = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { margin: 0; overflow: hidden; background-color: #111; font-family: sans-serif; cursor: crosshair; }
        #canvas-container { width: 100vw; height: 100vh; position: relative; }
        #hud {
            position: absolute;
            top: 20px;
            left: 20px;
            color: #00ff00;
            font-size: 15px;
            font-weight: bold;
            background: rgba(10, 15, 10, 0.88);
            padding: 18px 22px;
            border-radius: 8px;
            border: 1px solid #00ff00;
            line-height: 1.6;
            min-width: 250px;
            pointer-events: none;
            user-select: none;
            box-shadow: 0 0 15px rgba(0,255,0,0.2);
        }
        .hp-bar-container {
            width: 100%;
            background-color: #333;
            height: 16px;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 4px;
            border: 1px solid #666;
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
            color: #ff3333;
            font-size: 48px;
            font-weight: bold;
            background: rgba(0, 0, 0, 0.92);
            padding: 30px 50px;
            border: 3px solid #ff3333;
            border-radius: 12px;
            text-align: center;
            pointer-events: none;
            user-select: none;
            box-shadow: 0 0 25px rgba(255, 0, 0, 0.5);
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
            background: rgba(0, 0, 0, 0.85);
            padding: 10px 18px;
            border-radius: 10px;
            border: 1px solid #00ff00;
        }
        .tank-btn {
            background: #222;
            color: #ccc;
            border: 1px solid #444;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-weight: bold;
            transition: 0.2s;
        }
        .tank-btn:hover { background: #333; color: #fff; }
        .tank-btn.active {
            background: #00aa44;
            border-color: #00ff66;
            color: #fff;
            box-shadow: 0 0 10px rgba(0,255,100,0.5);
        }
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
</head>
<body>
    <div id="canvas-container">
        <div id="hud">
            <div>기종: <span id="tank-type-name" style="color: #ffff00;">경전차</span></div>
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

        <div id="tank-selector">
            <button class="tank-btn active" onclick="selectTankType('LIGHT')">[1] ⚡ 6륜 경전차 (고속/6바퀴)</button>
            <button class="tank-btn" onclick="selectTankType('MEDIUM')">[2] 🛡️ 중형전차 (주력)</button>
            <button class="tank-btn" onclick="selectTankType('HEAVY')">[3] 🐘 중전차 (DMG: 100 원샷!)</button>
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
        dirLight.shadow.mapSize.width = 2048;
        dirLight.shadow.mapSize.height = 2048;
        scene.add(dirLight);

        const gridHelper = new THREE.GridHelper(200, 50, 0x00ff00, 0x333333);
        gridHelper.position.y = -0.01;
        scene.add(gridHelper);

        const planeGeo = new THREE.PlaneGeometry(250, 250);
        const planeMat = new THREE.MeshStandardMaterial({ color: 0x1d2124, roughness: 0.8 });
        const plane = new THREE.Mesh(planeGeo, planeMat);
        plane.rotation.x = -Math.PI / 2;
        plane.receiveShadow = true;
        scene.add(plane);

        let playerHp = currentType.maxHp;
        let isGameOver = false;

        // --- 경전차(6륜 바퀴) 및 일반 무한궤도 탱크 메쉬 생성 함수 ---
        function createTankMesh(typeConfig, isAI = false) {
            const group = new THREE.Group();

            const darkMat = new THREE.MeshStandardMaterial({ color: 0x1a1a1a, roughness: 0.9 });
            const wheelMat = new THREE.MeshStandardMaterial({ color: 0x111111, roughness: 0.6, metalness: 0.4 });
            const bodyMat = new THREE.MeshStandardMaterial({ color: typeConfig.color, roughness: 0.5, metalness: 0.3 });
            const detailMat = new THREE.MeshStandardMaterial({ color: 0x222222, metalness: 0.8 });
            const lightMat = new THREE.MeshBasicMaterial({ color: isAI ? 0xff0000 : 0x00ffff });

            // 차체
            const bodyGeo = new THREE.BoxGeometry(3, 1.1, 4.2);
            const body = new THREE.Mesh(bodyGeo, bodyMat);
            body.position.y = 0.9;
            body.castShadow = true;
            group.add(body);

            if (typeConfig.isWheeled) {
                // **6륜 바퀴 구조 (좌 3개, 우 3개 = 총 6개)**
                const wheelPositionsZ = [-1.5, 0, 1.5]; // 앞, 중간, 뒤 바퀴 위치
                [-1.65, 1.65].forEach(x => {
                    wheelPositionsZ.forEach(z => {
                        const wheelGeo = new THREE.CylinderGeometry(0.52, 0.52, 0.5, 16);
                        const wheel = new THREE.Mesh(wheelGeo, wheelMat);
                        wheel.rotation.z = Math.PI / 2;
                        wheel.position.set(x, 0.52, z);
                        wheel.castShadow = true;
                        group.add(wheel);

                        // 휠 캡 디테일
                        const capGeo = new THREE.CylinderGeometry(0.2, 0.2, 0.52, 12);
                        const cap = new THREE.Mesh(capGeo, detailMat);
                        cap.rotation.z = Math.PI / 2;
                        cap.position.set(x, 0.52, z);
                        group.add(cap);
                    });
                });
            } else {
                // 무한궤도 구조 (중형/중전차)
                [-1.6, 1.6].forEach(x => {
                    const trackGeo = new THREE.BoxGeometry(0.6, 0.9, 4.6);
                    const track = new THREE.Mesh(trackGeo, darkMat);
                    track.position.set(x, 0.5, 0);
                    track.castShadow = true;
                    group.add(track);

                    for (let z = -1.8; z <= 1.8; z += 0.9) {
                        const wheelGeo = new THREE.CylinderGeometry(0.35, 0.35, 0.65, 12);
                        const wheel = new THREE.Mesh(wheelGeo, detailMat);
                        wheel.rotation.z = Math.PI / 2;
                        wheel.position.set(x, 0.4, z);
                        group.add(wheel);
                    }
                });
            }

            // 포탑
            const turretGroup = new THREE.Group();
            turretGroup.position.set(0, 1.65, 0.1);

            const turretGeo = new THREE.BoxGeometry(2.2, 0.75, 2.4);
            const turret = new THREE.Mesh(turretGeo, bodyMat);
            turret.position.set(0, 0, -0.2);
            turret.castShadow = true;
            turretGroup.add(turret);

            // 해치
            const hatchGeo = new THREE.CylinderGeometry(0.4, 0.4, 0.2, 12);
            const hatch = new THREE.Mesh(hatchGeo, detailMat);
            hatch.position.set(0.5, 0.45, -0.2);
            turretGroup.add(hatch);

            // 주포 Pitch 그룹
            const cannonPitchGroup = new THREE.Group();
            cannonPitchGroup.position.set(0, 0, 0.8);

            const cannonGeo = new THREE.CylinderGeometry(0.14, 0.16, 2.8, 16);
            const cannon = new THREE.Mesh(cannonGeo, detailMat);
            cannon.rotation.x = Math.PI / 2;
            cannon.position.set(0, 0, 1.2);
            cannon.castShadow = true;
            cannonPitchGroup.add(cannon);

            const muzzleGeo = new THREE.BoxGeometry(0.38, 0.38, 0.4);
            const muzzle = new THREE.Mesh(muzzleGeo, detailMat);
            muzzle.position.set(0, 0, 2.6);
            cannonPitchGroup.add(muzzle);

            turretGroup.add(cannonPitchGroup);

            [-0.9, 0.9].forEach(x => {
                const headLight = new THREE.Mesh(new THREE.BoxGeometry(0.2, 0.2, 0.1), lightMat);
                headLight.position.set(x, 1.0, 2.15);
                group.add(headLight);
            });

            group.add(turretGroup);

            return { 
                mesh: group, 
                turretGroup: turretGroup, 
                cannonPitchGroup: cannonPitchGroup 
            };
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

        function applyTankStats() {
            currentType = TANK_TYPES[currentTypeKey];
            rebuildPlayerTank();

            document.getElementById('tank-type-name').innerText = currentType.name;
            document.getElementById('tank-damage').innerText = currentType.damage;

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

        const aiTanks = [];
        function createAITank() {
            const aiData = createTankMesh(TANK_TYPES.MEDIUM, true);
            const aiMesh = aiData.mesh;

            const angle = Math.random() * Math.PI * 2;
            const distance = 30 + Math.random() * 30;
            aiMesh.position.set(
                playerTank.position.x + Math.sin(angle) * distance,
                0,
                playerTank.position.z + Math.cos(angle) * distance
            );

            scene.add(aiMesh);

            return {
                mesh: aiMesh,
                turretGroup: aiData.turretGroup,
                cannonPitchGroup: aiData.cannonPitchGroup,
                hp: 60,
                maxHp: 60,
                lastShootTime: 0,
                shootCooldown: 3.5 + Math.random() * 2
            };
        }

        for (let i = 0; i < 2; i++) aiTanks.push(createAITank());

        const healthPacks = [];
        function createHealthPack() {
            const packGroup = new THREE.Group();
            
            const packMat = new THREE.MeshStandardMaterial({ color: 0x00ff66, emissive: 0x00bb44 });
            const vMesh = new THREE.Mesh(new THREE.BoxGeometry(0.5, 1.6, 0.5), packMat);
            const hMesh = new THREE.Mesh(new THREE.BoxGeometry(1.6, 0.5, 0.5), packMat);
            packGroup.add(vMesh, hMesh);

            const pLight = new THREE.PointLight(0x00ff66, 1.5, 6);
            packGroup.add(pLight);

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

        for (let i = 0; i < 2; i++) healthPacks.push(createHealthPack());

        const bullets = [];
        const effects = [];
        const bulletGeo = new THREE.SphereGeometry(0.22, 8, 8);
        const heavyBulletGeo = new THREE.SphereGeometry(0.38, 12, 12);
        const playerBulletMat = new THREE.MeshBasicMaterial({ color: 0xffcc00 });
        const aiBulletMat = new THREE.MeshBasicMaterial({ color: 0xff3300 });

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
        const elevationAngleEl = document.getElementById('elevation-angle');
        const cameraStatusEl = document.getElementById('camera-status');
        const scoreStatusEl = document.getElementById('score-status');
        const hpTextEl = document.getElementById('hp-text');
        const hpBarEl = document.getElementById('hp-bar');
        const healMsgEl = document.getElementById('heal-msg');
        const gameOverEl = document.getElementById('game-over');

        function createMuzzleFlash(position, intensity = 3) {
            const flashLight = new THREE.PointLight(0xffaa00, intensity, 10);
            flashLight.position.copy(position);
            scene.add(flashLight);

            effects.push({ mesh: flashLight, life: 6 });
        }

        function updateHUD(currentTime) {
            hpTextEl.innerText = `${playerHp} / ${currentType.maxHp}`;
            const hpRatio = Math.max(0, playerHp / currentType.maxHp);
            hpBarEl.style.width = `${hpRatio * 100}%`;
            hpBarEl.style.backgroundColor = hpRatio > 0.5 ? "#00ff00" : (hpRatio > 0.25 ? "#ffaa00" : "#ff0000");

            engineStatusEl.innerText = isEngineOn ? "가동 중 [ON]" : "정지 [OFF - J입력]";
            engineStatusEl.style.color = isEngineOn ? "#00ff00" : "#ff3333";

            const remainingTime = currentType.cooldown - (currentTime - lastShootTime);
            if (remainingTime <= 0) {
                cooldownStatusEl.innerText = "발사 준비 완료";
                cooldownStatusEl.className = "ready";
            } else {
                cooldownStatusEl.innerText = `재장전 중... (${remainingTime.toFixed(1)}초)`;
                cooldownStatusEl.className = "cooldown";
            }

            const deg = (-cannonPitchGroup.rotation.x * (180 / Math.PI)).toFixed(1);
            elevationAngleEl.innerText = `${deg > 0 ? '+' : ''}${deg}°`;

            cameraStatusEl.innerText = isFirstPerson ? "1인칭 (조종석)" : "3인칭 (전체)";
            scoreStatusEl.innerText = killCount;
        }

        function restartGame() {
            playerHp = currentType.maxHp;
            isGameOver = false;
            killCount = 0;
            playerTank.position.set(0, 0, 0);
            playerTank.rotation.set(0, 0, 0);
            turretGroup.rotation.set(0, 0, 0);
            cannonPitchGroup.rotation.set(0, 0, 0);
            gameOverEl.style.display = "none";
            
            aiTanks.forEach(ai => scene.remove(ai.mesh));
            aiTanks.length = 0;
            for (let i = 0; i < 2; i++) aiTanks.push(createAITank());
        }

        function triggerFire() {
            if (isGameOver || !isEngineOn) return;
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

            createMuzzleFlash(muzzleOffset, isHeavy ? 6 : 3);

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

            if (isGameOver && key === 'r') restartGame();
            if (key === '1') selectTankType('LIGHT');
            else if (key === '2') selectTankType('MEDIUM');
            else if (key === '3') selectTankType('HEAVY');
            else if (key === 'j') isEngineOn = true;
            else if (key === 'h') isEngineOn = false;
            else if (key === 'f') triggerFire();
            else if (key === 'r') isFirstPerson = !isFirstPerson;
        });

        window.addEventListener('keyup', (e) => { keys[e.key.toLowerCase()] = false; });

        function animate() {
            requestAnimationFrame(animate);

            const now = performance.now() / 1000;
            updateHUD(now);

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

                const distanceHorizontal = Math.sqrt(localTarget.x * localTarget.x + localTarget.z * localTarget.z);
                const deltaY = localTarget.y - turretGroup.position.y;
                let targetPitch = -Math.atan2(deltaY, distanceHorizontal);

                const minPitch = -20 * (Math.PI / 180);
                const maxPitch = 15 * (Math.PI / 180);
                cannonPitchGroup.rotation.x = Math.max(minPitch, Math.min(maxPitch, targetPitch));

                for (let i = healthPacks.length - 1; i >= 0; i--) {
                    const pack = healthPacks[i];
                    pack.rotation.y += 0.03;

                    if (playerTank.position.distanceTo(pack.position) < 3.2) {
                        if (playerHp < currentType.maxHp) {
                            playerHp = Math.min(currentType.maxHp, playerHp + 30);
                            healMsgEl.style.display = "block";
                            setTimeout(() => { healMsgEl.style.display = "none"; }, 1200);

                            scene.remove(pack);
                            healthPacks.splice(i, 1);
                        }
                    }
                }

                if (now - lastPackSpawnTime > 12.0 && healthPacks.length < 3) {
                    lastPackSpawnTime = now;
                    healthPacks.push(createHealthPack());
                }

                aiTanks.forEach(ai => {
                    const targetPos = new THREE.Vector3(playerTank.position.x, ai.mesh.position.y, playerTank.position.z);
                    ai.mesh.lookAt(targetPos);

                    if (ai.mesh.position.distanceTo(playerTank.position) > 16) {
                        ai.mesh.translateZ(0.16);
                    }

                    if (now - ai.lastShootTime >= ai.shootCooldown) {
                        ai.lastShootTime = now;
                        fireBullet(ai.cannonPitchGroup, false, 18);
                    }
                });
            }

            for (let i = effects.length - 1; i >= 0; i--) {
                effects[i].life -= 1;
                if (effects[i].life <= 0) {
                    scene.remove(effects[i].mesh);
                    effects.splice(i, 1);
                }
            }

            for (let i = bullets.length - 1; i >= 0; i--) {
                const b = bullets[i];
                b.mesh.position.addScaledVector(b.direction, 0.7);
                b.life -= 1;

                if (!isGameOver) {
                    if (b.isPlayer) {
                        for (let j = aiTanks.length - 1; j >= 0; j--) {
                            const ai = aiTanks[j];
                            if (b.mesh.position.distanceTo(ai.mesh.position) < 2.6) {
                                ai.hp -= b.damage;
                                createMuzzleFlash(b.mesh.position, 4);

                                scene.remove(b.mesh);
                                bullets.splice(i, 1);

                                if (ai.hp <= 0) {
                                    scene.remove(ai.mesh);
                                    aiTanks.splice(j, 1);
                                    killCount += 1;
                                    setTimeout(() => { aiTanks.push(createAITank()); }, 2000);
                                }
                                break;
                            }
                        }
                    } else {
                        if (b.mesh.position.distanceTo(playerTank.position) < 2.6 * currentType.scale) {
                            playerHp -= b.damage;
                            createMuzzleFlash(b.mesh.position);

                            scene.remove(b.mesh);
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
                    bullets.splice(i, 1);
                }
            }

            if (isFirstPerson) {
                const fpOffset = new THREE.Vector3(0, 0.4 * currentType.scale, 0.4 * currentType.scale);
                fpOffset.applyMatrix4(cannonPitchGroup.matrixWorld);
                camera.position.copy(fpOffset);

                const lookAtOffset = new THREE.Vector3(0, 0.4 * currentType.scale, 20);
                lookAtOffset.applyMatrix4(cannonPitchGroup.matrixWorld);
                camera.lookAt(lookAtOffset);
            } else {
                const tpOffset = new THREE.Vector3(0, 6.5 * currentType.scale, -13 * currentType.scale);
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

components.html(html_code, height=700)
