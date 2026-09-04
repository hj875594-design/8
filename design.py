import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Streamlit 3D 탱크 시뮬레이션", layout="wide")

st.title("🚜 3D 탱크 시뮬레이터 (VS AI)")
st.caption("Streamlit + Three.js를 활용한 AI 탱크 대전 시뮬레이션")

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
    * **A**: 좌회전 | **D**: 우회전
    * **F**: 포탄 발사 🔥 (쿨타임 6초)
    * **R**: 시점 전환 🎥 (1인칭 ↔ 3인칭)
    """)

# 3D 캔버스 및 Three.js 게임 로직 HTML/JS
html_code = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { margin: 0; overflow: hidden; background-color: #1a1a1a; font-family: sans-serif; }
        #canvas-container { width: 100vw; height: 100vh; position: relative; }
        #hud {
            position: absolute;
            top: 20px;
            left: 20px;
            color: #00ff00;
            font-size: 18px;
            font-weight: bold;
            background: rgba(0, 0, 0, 0.75);
            padding: 12px 20px;
            border-radius: 8px;
            border: 1px solid #00ff00;
            line-height: 1.5;
        }
        .ready { color: #00ff00; }
        .cooldown { color: #ff9900; }
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
</head>
<body>
    <div id="canvas-container">
        <div id="hud">
            <div>엔진 상태: <span id="engine-status" style="color: #ff3333;">OFF (J를 눌러 시작)</span></div>
            <div>포탄 상태: <span id="cooldown-status" class="ready">발사 가능 [F]</span></div>
            <div>시점 모드: <span id="camera-status" style="color: #00ffff;">3인칭 [R로 변경]</span></div>
            <div>처치한 적 수: <span id="score-status" style="color: #ffff00;">0</span></div>
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

        // 플레이어 탱크 생성
        const playerTank = new THREE.Group();
        const bodyGeo = new THREE.BoxGeometry(3, 1.2, 4);
        const bodyMat = new THREE.MeshStandardMaterial({ color: 0x2e5a27 });
        const body = new THREE.Mesh(bodyGeo, bodyMat);
        body.position.y = 0.8;
        body.castShadow = true;
        playerTank.add(body);

        const turretGeo = new THREE.BoxGeometry(2, 0.8, 2);
        const turretMat = new THREE.MeshStandardMaterial({ color: 0x3d7534 });
        const turret = new THREE.Mesh(turretGeo, turretMat);
        turret.position.set(0, 1.8, -0.2);
        turret.castShadow = true;
        playerTank.add(turret);

        const cannonGeo = new THREE.CylinderGeometry(0.15, 0.15, 2.5, 16);
        const cannonMat = new THREE.MeshStandardMaterial({ color: 0x111111 });
        const cannon = new THREE.Mesh(cannonGeo, cannonMat);
        cannon.rotation.x = Math.PI / 2;
        cannon.position.set(0, 1.8, 1.5);
        cannon.castShadow = true;
        playerTank.add(cannon);

        scene.add(playerTank);

        // AI 탱크 팩토리 함수
        const aiTanks = [];
        const aiBodyMat = new THREE.MeshStandardMaterial({ color: 0x8b0000 });
        const aiTurretMat = new THREE.MeshStandardMaterial({ color: 0xb22222 });

        function createAITank() {
            const aiTank = new THREE.Group();
            
            const aiBody = new THREE.Mesh(bodyGeo, aiBodyMat);
            aiBody.position.y = 0.8;
            aiBody.castShadow = true;
            aiTank.add(aiBody);

            const aiTurret = new THREE.Mesh(turretGeo, aiTurretMat);
            aiTurret.position.set(0, 1.8, -0.2);
            aiTurret.castShadow = true;
            aiTank.add(aiTurret);

            const aiCannon = new THREE.Mesh(cannonGeo, cannonMat);
            aiCannon.rotation.x = Math.PI / 2;
            aiCannon.position.set(0, 1.8, 1.5);
            aiCannon.castShadow = true;
            aiTank.add(aiCannon);

            // 랜덤 생성 위치 (플레이어와 거리를 둠)
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
                lastShootTime: 0,
                shootCooldown: 4.0 + Math.random() * 2 // 4~6초마다 무작위 발사
            };
        }

        // 초기 AI 탱크 2대 생성
        for (let i = 0; i < 2; i++) {
            aiTanks.push(createAITank());
        }

        // 포탄 관리
        const bullets = [];
        const bulletGeo = new THREE.SphereGeometry(0.25, 8, 8);
        const playerBulletMat = new THREE.MeshStandardMaterial({ color: 0xffa500, emissive: 0xff3300 });
        const aiBulletMat = new THREE.MeshStandardMaterial({ color: 0xff0000, emissive: 0xaa0000 });

        // 상태 및 제어 변수
        let isEngineOn = false;
        let isFirstPerson = false;
        let killCount = 0;
        const keys = {};
        const speed = 0.15;
        const turnSpeed = 0.03;
        const bulletSpeed = 1.2;

        const COOLDOWN_TIME = 6.0;
        let lastShootTime = -COOLDOWN_TIME;

        const engineStatusEl = document.getElementById('engine-status');
        const cooldownStatusEl = document.getElementById('cooldown-status');
        const cameraStatusEl = document.getElementById('camera-status');
        const scoreStatusEl = document.getElementById('score-status');

        function updateHUD(currentTime) {
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
                cooldownStatusEl.innerText = "발사 가능 [F]";
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

        // 포탄 발사 함수 (플레이어/AI 공용)
        function fireBullet(tankGroup, isPlayer, currentTime) {
            const bullet = new THREE.Mesh(bulletGeo, isPlayer ? playerBulletMat : aiBulletMat);
            
            const muzzleOffset = new THREE.Vector3(0, 1.8, 2.8);
            muzzleOffset.applyMatrix4(tankGroup.matrixWorld);
            bullet.position.copy(muzzleOffset);

            const direction = new THREE.Vector3(0, 0, 1);
            direction.applyQuaternion(tankGroup.quaternion).normalize();

            bullets.push({
                mesh: bullet,
                direction: direction,
                isPlayer: isPlayer,
                life: 120
            });

            scene.add(bullet);
        }

        window.addEventListener('keydown', (e) => {
            const key = e.key.toLowerCase();
            keys[key] = true;
            const now = performance.now() / 1000;

            if (key === 'j') {
                isEngineOn = true;
            } else if (key === 'h') {
                isEngineOn = false;
            } else if (key === 'f' && isEngineOn) {
                if (now - lastShootTime >= COOLDOWN_TIME) {
                    lastShootTime = now;
                    fireBullet(playerTank, true, now);
                }
            } else if (key === 'r') {
                isFirstPerson = !isFirstPerson;
            }
        });

        window.addEventListener('keyup', (e) => {
            keys[e.key.toLowerCase()] = false;
        });

        // 애니메이션 루프
        function animate() {
            requestAnimationFrame(animate);

            const now = performance.now() / 1000;
            updateHUD(now);

            // 플레이어 조종
            if (isEngineOn) {
                if (keys['w']) playerTank.translateZ(speed);
                if (keys['s']) playerTank.translateZ(-speed);
                if (keys['a']) playerTank.rotation.y += turnSpeed;
                if (keys['d']) playerTank.rotation.y -= turnSpeed;
            }

            // AI 탱크 추적 및 공격 로직
            aiTanks.forEach(ai => {
                // 플레이어를 바라보도록 회전
                const targetPosition = new THREE.Vector3(playerTank.position.x, ai.mesh.position.y, playerTank.position.z);
                ai.mesh.lookAt(targetPosition);

                // 일정 거리 유지하며 접근 (15 유닛 거리까지)
                const dist = ai.mesh.position.distanceTo(playerTank.position);
                if (dist > 15) {
                    ai.mesh.translateZ(speed * 0.5); // 플레이어보다 절반 속도로 이동
                }

                // AI 포탄 발사
                if (now - ai.lastShootTime >= ai.shootCooldown) {
                    ai.lastShootTime = now;
                    fireBullet(ai.mesh, false, now);
                }
            });

            // 포탄 이동 및 충돌 판정
            for (let i = bullets.length - 1; i >= 0; i--) {
                const b = bullets[i];
                b.mesh.position.addScaledVector(b.direction, bulletSpeed);
                b.life -= 1;

                // 플레이어 포탄이 AI 탱크에 적중했는지 체크
                if (b.isPlayer) {
                    for (let j = aiTanks.length - 1; j >= 0; j--) {
                        const ai = aiTanks[j];
                        if (b.mesh.position.distanceTo(ai.mesh.position) < 2.5) {
                            // AI 탱크 파괴
                            scene.remove(ai.mesh);
                            aiTanks.splice(j, 1);

                            // 포탄 제거
                            scene.remove(b.mesh);
                            b.mesh.geometry.dispose();
                            bullets.splice(i, 1);

                            killCount += 1;

                            // 새 AI 탱크 리스폰
                            setTimeout(() => {
                                aiTanks.push(createAITank());
                            }, 2000);
                            break;
                        }
                    }
                }

                // 수명 다한 포탄 제거
                if (b.life <= 0) {
                    scene.remove(b.mesh);
                    b.mesh.geometry.dispose();
                    bullets.splice(i, 1);
                }
            }

            // 카메라 위치 설정
            if (isFirstPerson) {
                const fpOffset = new THREE.Vector3(0, 2.0, 0.5);
                const fpPosition = fpOffset.applyMatrix4(playerTank.matrixWorld);
                camera.position.copy(fpPosition);

                const lookAtOffset = new THREE.Vector3(0, 2.0, 20);
                const lookAtPosition = lookAtOffset.applyMatrix4(playerTank.matrixWorld);
                camera.lookAt(lookAtPosition);
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

# Streamlit 내에 3D Render 컴포넌트 렌더링
components.html(html_code, height=650)
