import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Streamlit 3D 탱크 시뮬레이션", layout="wide")

st.title("🚜 3D 탱크 시뮬레이터")
st.caption("Streamlit + Three.js를 활용한 실시간 3D 탱크 조종 및 시점 전환")

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
        </div>
    </div>

    <script>
        // 기본 3D 씬 설정
        const container = document.getElementById('canvas-container');
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x1a1a1a);

        const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.shadowMap.enabled = true;
        container.appendChild(renderer.domElement);

        // 조명
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        scene.add(ambientLight);

        const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
        dirLight.position.set(20, 40, 20);
        dirLight.castShadow = true;
        scene.add(dirLight);

        // 바닥 (지형)
        const gridHelper = new THREE.GridHelper(200, 50, 0x00ff00, 0x444444);
        gridHelper.position.y = -0.01;
        scene.add(gridHelper);

        const planeGeo = new THREE.PlaneGeometry(200, 200);
        const planeMat = new THREE.MeshStandardMaterial({ color: 0x222222 });
        const plane = new THREE.Mesh(planeGeo, planeMat);
        plane.rotation.x = -Math.PI / 2;
        plane.receiveShadow = true;
        scene.add(plane);

        // 탱크 개체 생성 (Group)
        const tank = new THREE.Group();

        // 탱크 차체 (Body)
        const bodyGeo = new THREE.BoxGeometry(3, 1.2, 4);
        const bodyMat = new THREE.MeshStandardMaterial({ color: 0x2e5a27 });
        const body = new THREE.Mesh(bodyGeo, bodyMat);
        body.position.y = 0.8;
        body.castShadow = true;
        tank.add(body);

        // 포탑 (Turret)
        const turretGeo = new THREE.BoxGeometry(2, 0.8, 2);
        const turretMat = new THREE.MeshStandardMaterial({ color: 0x3d7534 });
        const turret = new THREE.Mesh(turretGeo, turretMat);
        turret.position.set(0, 1.8, -0.2);
        turret.castShadow = true;
        tank.add(turret);

        // 포신 (Cannon)
        const cannonGeo = new THREE.CylinderGeometry(0.15, 0.15, 2.5, 16);
        const cannonMat = new THREE.MeshStandardMaterial({ color: 0x111111 });
        const cannon = new THREE.Mesh(cannonGeo, cannonMat);
        cannon.rotation.x = Math.PI / 2;
        cannon.position.set(0, 1.8, 1.5);
        cannon.castShadow = true;
        tank.add(cannon);

        scene.add(tank);

        // 포탄 배열 및 리소스
        const bullets = [];
        const bulletGeo = new THREE.SphereGeometry(0.25, 8, 8);
        const bulletMat = new THREE.MeshStandardMaterial({ color: 0xffa500, emissive: 0xff3300 });

        // 상태 및 제어 변수
        let isEngineOn = false;
        let isFirstPerson = false; // 1인칭 시점 여부 플래그
        const keys = {};
        const speed = 0.15;
        const turnSpeed = 0.03;
        const bulletSpeed = 1.2;

        const COOLDOWN_TIME = 6.0;
        let lastShootTime = -COOLDOWN_TIME;

        // UI 엘리먼트
        const engineStatusEl = document.getElementById('engine-status');
        const cooldownStatusEl = document.getElementById('cooldown-status');
        const cameraStatusEl = document.getElementById('camera-status');

        function updateHUD(currentTime) {
            // 엔진 상태
            if (isEngineOn) {
                engineStatusEl.innerText = "ON";
                engineStatusEl.style.color = "#00ff00";
            } else {
                engineStatusEl.innerText = "OFF (J를 눌러 시작)";
                engineStatusEl.style.color = "#ff3333";
            }

            // 쿨타임 상태
            const elapsedTime = currentTime - lastShootTime;
            const remainingTime = COOLDOWN_TIME - elapsedTime;

            if (remainingTime <= 0) {
                cooldownStatusEl.innerText = "발사 가능 [F]";
                cooldownStatusEl.className = "ready";
            } else {
                cooldownStatusEl.innerText = `재장전 중... (${remainingTime.toFixed(1)}초)`;
                cooldownStatusEl.className = "cooldown";
            }

            // 시점 상태
            if (isFirstPerson) {
                cameraStatusEl.innerText = "1인칭 (조종석)";
                cameraStatusEl.style.color = "#ff00ff";
            } else {
                cameraStatusEl.innerText = "3인칭 (전체 뷰)";
                cameraStatusEl.style.color = "#00ffff";
            }
        }

        // 포탄 발사 함수
        function fireBullet(currentTime) {
            if (!isEngineOn) return;

            if (currentTime - lastShootTime < COOLDOWN_TIME) {
                return;
            }

            lastShootTime = currentTime;

            const bullet = new THREE.Mesh(bulletGeo, bulletMat);
            
            const muzzleOffset = new THREE.Vector3(0, 1.8, 2.8);
            muzzleOffset.applyMatrix4(tank.matrixWorld);
            bullet.position.copy(muzzleOffset);

            const direction = new THREE.Vector3(0, 0, 1);
            direction.applyQuaternion(tank.quaternion).normalize();

            bullets.push({
                mesh: bullet,
                direction: direction,
                life: 120
            });

            scene.add(bullet);
        }

        // 키보드 이벤트
        window.addEventListener('keydown', (e) => {
            const key = e.key.toLowerCase();
            keys[key] = true;

            const now = performance.now() / 1000;

            if (key === 'j') {
                isEngineOn = true;
            } else if (key === 'h') {
                isEngineOn = false;
            } else if (key === 'f') {
                fireBullet(now);
            } else if (key === 'r') {
                isFirstPerson = !isFirstPerson; // R 키 입력 시 시점 전환
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

            if (isEngineOn) {
                if (keys['w']) tank.translateZ(speed);
                if (keys['s']) tank.translateZ(-speed);
                if (keys['a']) tank.rotation.y += turnSpeed;
                if (keys['d']) tank.rotation.y -= turnSpeed;
            }

            // 포탄 이동 처리
            for (let i = bullets.length - 1; i >= 0; i--) {
                const b = bullets[i];
                b.mesh.position.addScaledVector(b.direction, bulletSpeed);
                b.life -= 1;

                if (b.life <= 0) {
                    scene.remove(b.mesh);
                    b.mesh.geometry.dispose();
                    bullets.splice(i, 1);
                }
            }

            // 시점(카메라 위치) 변경 처리
            if (isFirstPerson) {
                // 1인칭: 포탑 바로 위 약간 앞쪽에 카메라 위치
                const fpOffset = new THREE.Vector3(0, 2.0, 0.5);
                const fpPosition = fpOffset.applyMatrix4(tank.matrixWorld);
                camera.position.copy(fpPosition);

                // 시선 방향: 탱크 정면을 바라봄
                const lookAtOffset = new THREE.Vector3(0, 2.0, 20);
                const lookAtPosition = lookAtOffset.applyMatrix4(tank.matrixWorld);
                camera.lookAt(lookAtPosition);
            } else {
                // 3인칭: 탱크 뒤쪽 위에서 추적
                const tpOffset = new THREE.Vector3(0, 6, -12);
                const tpPosition = tpOffset.applyMatrix4(tank.matrixWorld);
                camera.position.copy(tpPosition);
                camera.lookAt(tank.position.x, tank.position.y + 1, tank.position.z);
            }

            renderer.render(scene, camera);
        }

        // 윈도우 리사이즈 대응
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
