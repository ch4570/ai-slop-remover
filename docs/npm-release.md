# npm 배포

패키지: `lutriva`. 기본 CLI는 `lutriva`이고 `ai-slop-remover`도 같은 구현을 호출한다. 기존 스킬 ID와 설치 기록은 유지한다. 이전 패키지명 `ai-slop-remover-skills`와 다른 프로젝트가 사용하는 `ai-slop-remover` 이름으로 게시하지 않는다.

현재 npm 레지스트리 게시는 대기 중이다. 저장소의 버전 변경이나 GitHub 태그만으로 npm 게시가 완료되지는 않는다.

## 검증과 게시

소스 체크아웃에서 실행한다. 패키지와 manifest 버전을 함께 확인하고, 기존 게시 버전은 덮어쓰지 않는다.

```bash
python3 scripts/update_manifest.py --check
npm test
python3 -m unittest discover -s tests -q
npm pack --dry-run
npm whoami --registry=https://registry.npmjs.org/
npm publish --access public --registry=https://registry.npmjs.org/
npm view lutriva version dist-tags --json
```

`prepack`은 manifest·패키지 검사를, `prepublishOnly`는 npm CLI 테스트와 Python 회귀 테스트를 실행한다. 검증 실패를 `--ignore-scripts`로 우회해서 게시하지 않는다.

인증이 없으면 로컬 터미널에서 `npm login --registry=https://registry.npmjs.org/`으로 로그인한다. 비밀번호·토큰·OTP를 저장소나 채팅에 기록하지 않는다. 계정의 보안 설정에 따라 게시 시 추가 인증이 필요할 수 있다.

게시 성공 후 레지스트리의 버전·무결성을 확인하고, 새 임시 프로젝트에서 `npx lutriva@2.4.0 --list`와 설치를 검증한다. 로컬 tarball 검증과 실제 레지스트리 설치 검증은 구분해서 보고한다.
