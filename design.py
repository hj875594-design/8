import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Streamlit 3D 탱크 시뮬레이션", layout="wide")

st.title("🚜 3D 탱크 대전 시뮬레이터 (기종별 전용 디자인 적용)")
st.caption("각 기종의 명칭에 맞춰 독자적인 외형(미사일 포드, 궤도 장갑, 쌍열 주포)이 적용되었습니다.")

col1, col2 = st.columns(2)
with col1:
    st.markdown("""
    **[시스템 조작]**
    * **ESC**: 일시정지 / 메인 메뉴 전환 ⏸️
    * **J / H**: 엔진 시작 / 정지
    * **1 / 2 / 3**: 기종 변경 (스카우트 랭거 / MBT 치프틴 / 베히모스)
    """)
with col2:
    st.markdown("""
    **[전투 조종]**
    * **W / A / S / D**: 이동 및 차체 회전
    * **마우스 이동**: 포탑 조준 | **좌클릭 / F**: 포탄 발사 🔥
    * **R**: 1/3인칭 시점 전환
    """)

html_code = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { margin: 0; overflow: hidden; background-color: #0b0d10; font-family: 'Segoe UI', sans-serif; cursor: default; }
        #canvas-container { width: 100vw; height: 100vh; position: relative; }
        
        #home-screen {
            position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(10, 14, 20, 0.94); display: flex; flex-direction: column;
            justify-content: center; align-items: center; z-index: 100; backdrop-filter: blur(8px);
        }
        .title { font-size: 48px; font-weight: 900; color: #00ff66; text-shadow: 0 0 20px rgba(0, 255, 102, 0.6); letter-spacing: 2px; margin-bottom: 8px; }
        .subtitle { font-size: 16px; color: #aaa; margin-bottom: 35px; }
        .select-title { font-size: 18px; color: #fff; margin-bottom: 15px; font-weight: bold; }
        
        .tank-option-group { display: flex; gap: 20px; margin-bottom: 35px; }
        .tank-card {
            background: rgba(255,255,255,0.05); border: 2px solid #333; border-radius: 12px;
            padding: 20px; width: 200px; text-align: center; cursor: pointer; transition: all 0.2s ease;
        }
        .tank-card:hover { border-color: #00ff66; transform: translateY(-5px); background: rgba(0, 255, 102, 0.1); }
        .tank-card.selected { border-color: #00ff66; background: rgba(0, 255, 102, 0.2); box-shadow: 0 0 15px rgba(0, 255, 102, 0.4); }
        .tank-card h3 { margin: 0 0 8px 0; color: #fff; font-size: 17px; }
        .tank-card p { margin: 4px 0; color: #bbb; font-size: 12px; }

        .btn-start {
            background: #00aa44; color: #fff; font-size: 22px; font-weight: bold;
            padding: 14px 45px; border: 2px solid #00ff66; border-radius: 30px;
            cursor: pointer; box-shadow: 0 0 20px rgba(0,255,100,0.4); transition: 0.2s;
        }
        .btn-start:hover { background: #00ff66; color: #000; box-shadow: 0 0 30px rgba(0,255,102,0.8); transform: scale(1.05); }

        #pause-screen {
            display: none; position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.85); flex-direction: column; justify-content: center; align-items: center; z-index: 90;
        }
        .pause-title { font-size: 40px; color: #fff; margin-bottom: 30px; }
        .pause-btn {
            background: #222; color: #fff; border: 1px solid #555; padding: 12px 30px;
            margin: 8px; font-size: 18px; font-weight: bold; border-radius: 8px; cursor: pointer; transition: 0.2s;
        }
        .pause-btn:hover { background: #00ff66; color: #000; border-color: #00ff66; }

        #hud {
            position: absolute; top: 20px; left: 20px; color: #00ff00; font-size: 14px; font-weight: bold;
            background: rgba(10, 15, 10, 0.88); padding: 18px 22px; border-radius: 8px;
            border: 1px solid #00ff00; line-height: 1.6; min-width: 260px; pointer-events: none;
            box-shadow: 0 0 15px rgba(0,255,0,0.2); display: none;
        }
        .hp-bar-container { width: 100%; background-color: #333; height: 14px; border-radius: 4px; overflow: hidden; margin-top: 4px; border: 1px solid #666; }
        .hp-bar-fill { height: 100%; background-color: #00ff00; width: 100%; transition: width 0.2s; }

        #game-over {
            display: none; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
            color: #ff3333; font-size: 48px; font-weight: bold; background: rgba(0, 0, 0, 0.92);
            padding: 30px 50px; border: 3px solid #ff3333; border-radius: 12px; text-align: center; z-index: 80;
        }
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
</head>
<body>
    <div id="canvas-container">
        <div id="home-screen">
            <div class="title">ARMORED WARFARE 3D</div>
            <div class="subtitle">개성 넘치는 기종별 독자 디자인 전차를 확인하고 선택하세요</div>

            <div class="select-title">기종 명칭 및 디자인 선택</div>
            <div class="tank-option-group">
                <div class="tank-card selected" id="card-LIGHT" onclick="homeSelectTank('LIGHT')">
                    <h3>⚡ 스카우트 T-7 "랭거"</h3>
                    <p><b>6륜 장갑 / 미사일 포드</b></p>
                    <p>기동성: 최상 (고속 정찰)</p>
                    <p>DMG: 20</p>
                </div>
                <div class="tank-card" id="card-MEDIUM" onclick="homeSelectTank('MEDIUM')">
                    <h3>🛡️ MBT-12 "치프틴"</h3>
                    <p><b>복합 측면장갑 / 연막탄</b></p>
                    <p>기동성: 보통 (주력 전차)</p>
                    <p>DMG: 30</p>
                </div>
                <div class="tank-card" id="card-HEAVY" onclick="homeSelectTank('HEAVY')">
                    <h3>🐘 HT-9 "베히모스"</h3>
                    <p><b>쌍열 주포 / 반응 장갑</b></p>
                    <p>기동성: 느림 (원샷 원킬)</p>
                    <p>DMG: 100</p>
                </div>
            </div>

            <button class="btn-start" onclick="startGame()">전장 출격 (START)</button>
        </div>

        <div id="pause-screen">
            <div class="pause-title">PAUSED</div>
            <button class="pause-btn" onclick="resumeGame()">전투 재개 (Resume)</button>
            <button class="pause-btn" onclick="returnToHome()">메인 메뉴로 (Home)</button>
        </div>

        <div id="hud">
            <div>기종: <span id="tank-type-name" style="color: #ffff00;">스카우트 T-7 '랭거'</span></div>
            <div>주포 데미지: <span id="tank-damage" style="color: #ff3300;">20</span></div>
            <div>내구도: <span id="hp-text">70 / 70</span>
                <div class="hp-bar-container"><div id="hp-bar" class="hp-bar-fill"></div></div>
            </div>
            <div style="margin-top: 8px;">동력계: <span id="engine-status" style="color: #ff3333;">정지 [J: 시동]</span></div>
            <div>주포 상태: <span id="cooldown-status" style="color: #00ff00;">발사 준비 완료</span></div>
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
            LIGHT: { name: "스카우트 T-7 '랭거'", maxHp: 70, speed: 0.45, turnSpeed: 0.07, damage: 20, cooldown: 3.5, color: 0x3d5236, scale: 0.8 },
            MEDIUM: { name: "MBT-12 '치프틴'", maxHp: 100, speed: 0.30, turnSpeed: 0.05, damage: 30, cooldown: 5.5, color: 0x2e4f25, scale: 1.0 },
            HEAVY: { name: "HT-9 '베히모스'", maxHp: 160, speed: 0.18, turnSpeed: 0.035, damage: 100, cooldown: 7.5, color: 0x1f2e22, scale: 1.25 }
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

        scene.add(new THREE.AmbientLight(0xffffff, 0.6));
        const dirLight = new THREE.DirectionalLight(0xfff5ea, 1.2);
        dirLight.position.set(30, 50, 20);
        dirLight.castShadow = true;
        scene.add(dirLight);

        const plane = new THREE.Mesh(
            new THREE.PlaneGeometry(250, 250),
            new THREE.MeshStandardMaterial({ color: 0x1d2124, roughness: 0.8 })
        );
        plane.rotation.x = -Math.PI / 2;
        plane.receiveShadow = true;
        scene.add(plane);

        let playerHp = currentType.maxHp;
        let isGameOver = false;

        // --- 명칭에 맞춘 고유 디자인 생성 로직 ---
        function createCustomTankMesh(typeKey, isAI = false) {
            const group = new THREE.Group();
            const config = TANK_TYPES[typeKey];

            const bodyMat = new THREE.MeshStandardMaterial({ color: isAI ? 0x772222 : config.color, roughness: 0.5, metalness: 0.3 });
            const darkMat = new THREE.MeshStandardMaterial({ color: 0x111111, metalness: 0.8, roughness: 0.4 });
            const metalMat = new THREE.MeshStandardMaterial({ color: 0x333333, metalness: 0.9, roughness: 0.2 });
            const lightMat = new THREE.MeshBasicMaterial({ color: isAI ? 0xff0000 : 0x00ffff });

            // 1. 차체 (Base Body)
            const body = new THREE.Mesh(new THREE.BoxGeometry(3.0, 1.1, 4.4), bodyMat);
            body.position.y = 0.9;
            body.castShadow = true;
            group.add(body);

            const turretGroup = new THREE.Group();
            turretGroup.position.set(0, 1.65, 0.1);
            const cannonPitchGroup = new THREE.Group();
            cannonPitchGroup.position.set(0, 0, 0.8);

            // ==================== ⚡ 1. 스카우트 T-7 "랭거" (6륜 장갑/미사일 포드) ====================
            if (typeKey === 'LIGHT') {
                // 6바퀴
                [-1.65, 1.65].forEach(x => {
                    [-1.5, 0, 1.5].forEach(z => {
                        const wheel = new THREE.Mesh(new THREE.CylinderGeometry(0.52, 0.52, 0.45, 16), darkMat);
                        wheel.rotation.z = Math.PI / 2;
                        wheel.position.set(x, 0.52, z);
                        group.add(wheel);
                    });
                });

                // 미사일 포드 (포탑 양옆)
                [-1.4, 1.4].forEach(x => {
                    const pod = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.5, 1.2), metalMat);
                    pod.position.set(x, 0.2, -0.1);
                    turretGroup.add(pod);
                });

                // 상부 서치라이트/탐조등
                const lightSpot = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.2, 0.3, 12), lightMat);
                lightSpot.rotation.x = Math.PI / 2;
                lightSpot.position.set(-0.6, 0.5, 0.5);
                turretGroup.add(lightSpot);

                // 단열 고속 주포
                const cannon = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.14, 2.8, 16), metalMat);
                cannon.rotation.x = Math.PI / 2;
                cannon.position.set(0, 0, 1.2);
                cannonPitchGroup.add(cannon);

                const turret = new THREE.Mesh(new THREE.BoxGeometry(2.0, 0.7, 2.2), bodyMat);
                turretGroup.add(turret);
            }

            // ==================== 🛡️ 2. MBT-12 "치프틴" (복합 장갑/연막탄 발사기) ====================
            else if (typeKey === 'MEDIUM') {
                // 무한궤도 + 사이드 스커트(복합장갑 판넬)
                [-1.6, 1.6].forEach(x => {
                    const track = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.85, 4.6), darkMat);
                    track.position.set(x, 0.5, 0);
                    group.add(track);

                    // 측면 보호 장갑판 (Side Skirts)
                    const skirt = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.7, 4.4), bodyMat);
                    skirt.position.set(x > 0 ? x + 0.3 : x - 0.3, 0.7, 0);
                    group.add(skirt);
                });

                // 포탑 측면 연막탄 발사기 기믹
                [-1.25, 1.25].forEach(x => {
                    const smokeLauncher = new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.3, 0.6), metalMat);
                    smokeLauncher.position.set(x, 0.2, -0.4);
                    smokeLauncher.rotation.y = x > 0 ? -0.3 : 0.3;
                    turretGroup.add(smokeLauncher);
                });

                // 주포 및 제퇴기
                const cannon = new THREE.Mesh(new THREE.CylinderGeometry(0.15, 0.17, 3.2, 16), metalMat);
                cannon.rotation.x = Math.PI / 2;
                cannon.position.set(0, 0, 1.4);
                cannonPitchGroup.add(cannon);

                const turret = new THREE.Mesh(new THREE.BoxGeometry(2.3, 0.75, 2.5), bodyMat);
                turretGroup.add(turret);
            }

            // ==================== 🐘 3. HT-9 "베히모스" (쌍열 주포/이중 반응장갑) ====================
            else if (typeKey === 'HEAVY') {
                // 더 두꺼운 무한궤도
                [-1.75, 1.75].forEach(x => {
                    const track = new THREE.Mesh(new THREE.BoxGeometry(0.75, 0.95, 4.8), darkMat);
                    track.position.set(x, 0.5, 0);
                    group.add(track);
                });

                // 전면 및 측면 반응장갑(ERA) 블록 부착
                for (let z = -1.5; z <= 1.5; z += 0.8) {
                    [-1.6, 1.6].forEach(x => {
                        const eraBlock = new THREE.Mesh(new THREE.BoxGeometry(0.2, 0.3, 0.6), metalMat);
                        eraBlock.position.set(x, 0.95, z);
                        group.add(eraBlock);
                    });
                }

                // 🔥 **핵심: 쌍열 주포 (Double Cannon)**
                [-0.35, 0.35].forEach(x => {
                    const cannon = new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.18, 3.4, 16), metalMat);
                    cannon.rotation.x = Math.PI / 2;
                    cannon.position.set(x, 0, 1.5);
                    cannonPitchGroup.add(cannon);

                    const muzzle = new THREE.Mesh(new THREE.BoxGeometry(0.4, 0.4, 0.5), metalMat);
                    muzzle.position.set(x, 0, 3.1);
                    cannonPitchGroup.add(muzzle);
                });

                const turret = new THREE.Mesh(new THREE.BoxGeometry(2.7, 0.85, 2.8), bodyMat);
                turretGroup.add(turret);
            }

            turretGroup.add(cannonPitchGroup);
            group.add(turretGroup);

            // 헤드라이트
            [-0.9, 0.9].forEach(x => {
                const hl = new THREE.Mesh(new THREE.BoxGeometry(0.2, 0.2, 0.1), lightMat);
                hl.position.set(x, 1.0, 2.2);
                group.add(hl);
            });

            return { mesh: group, turretGroup, cannonPitchGroup };
        }

        let playerTankData = createCustomTankMesh(currentTypeKey, false);
        let playerTank = playerTankData.mesh;
        let turretGroup = playerTankData.turretGroup;
        let cannonPitchGroup = playerTankData.cannonPitchGroup;
        scene.add(playerTank);

        function rebuildPlayerTank() {
            scene.remove(playerTank);
            playerTankData = createCustomTankMesh(currentTypeKey, false);
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
            isPaused = false; isGameStarted = false;
            document.getElementById('pause-screen').style.display = 'none';
            document.getElementById('hud').style.display = 'none';
            document.getElementById('home-screen').style.display = 'flex';
            document.body.style.cursor = 'default';
        }

        const aiTanks = [];
        function createAITank() {
            const aiData = createCustomTankMesh('MEDIUM', true);
            const aiMesh = aiData.mesh;
            const angle = Math.random() * Math.PI * 2;
            const distance = 30 + Math.random() * 30;
            aiMesh.position.set(Math.sin(angle) * distance, 0, Math.cos(angle) * distance);
            scene.add(aiMesh);
            return { mesh: aiMesh, turretGroup: aiData.turretGroup, cannonPitchGroup: aiData.cannonPitchGroup, hp: 60, lastShootTime: 0, shootCooldown: 4 };
        }

        const bullets = [];
        const bulletGeo = new THREE.SphereGeometry(0.22, 8, 8);
        const heavyBulletGeo = new THREE.SphereGeometry(0.40, 12, 12);
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
            isGameOver = false; killCount = 0;
            playerTank.position.set(0, 0, 0); playerTank.rotation.set(0, 0, 0);
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
            const muzzleOffset = new THREE.Vector3(0, 0, 3.0 * (isPlayer ? currentType.scale : 1.0));
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
                if (!isGameStarted) {
                    const time = Date.now() * 0.0006;
                    camera.position.x = Math.sin(time) * 11;
                    camera.position.z = Math.cos(time) * 11;
                    camera.position.y = 5.5;
                    camera.lookAt(0, 1, 0);
                }
                renderer.render(scene, camera);
                return;
            }

            document.getElementById('tank-type-name').innerText = currentType.name;
            document.getElementById('tank-damage').innerText = currentType.damage;
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
                    const now = performance.now() / 1000;
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
                camera.position.copy(tpPosition);
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
