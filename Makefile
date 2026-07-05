IMAGE ?= robotomonojp:dev
CONFIG ?= config/plex.yaml
OUTPUT ?= dist
FAMILY ?= RobotoMonoPlex

# print のデフォルト. TEXT は 英数字 / ひらがな (濁点・半濁点) / カタカナ / 半角カナ /
# 漢字 / 全角英数・全角記号 / 曖昧幅記号 / Nerd Fonts をsource別 (Pomicons, Powerline,
# FA Extension, Weather, Seti-UI, Devicons, Codicons, Font Awesome, Octicons,
# Font Logos, Material Design, IEC Power) に網羅する.
FONT ?= $(OUTPUT)/$(FAMILY)/$(FAMILY)-Regular.ttf
TEXT ?= AZaz09 あいがぱ アヴパ ｱｲｶﾞﾊﾟ 漢字日本語鬱 Ａ１。、「」￥ ○●■◆★→※±×÷ ⏻           󰀂
OUT ?= preview.pdf
DOCKER_RUN = docker run --rm -v $(PWD):/app -w /app $(IMAGE)

.PHONY: help
help:
	@echo "make submodule-init  # Nerd Fonts submoduleを sparse-checkout 込みで初期化"
	@echo "make docker-build    # Dockerイメージをbuild"
	@echo "make generate CONFIG=config/{font}.yaml  # 8ファイル生成 (デフォルト config/plex.yaml)"
	@echo "make generate-regular  # Regular だけ生成 (デバッグ用)"
	@echo "make reinstall-macos-fonts FAMILY=...  # 既存FAMILYを削除してdistをmacOSに再インストール"
	@echo "make print [FONT=... TEXT=... OUT=...]  # フォント確認PDFを生成 (デフォルトで全文字種を網羅)"
	@echo "make lint            # ruff format --check + ruff check"
	@echo "make format          # ruff format"
	@echo "make test            # pytest"

.PHONY: submodule-init
submodule-init:
	git submodule update --init --no-fetch --checkout vendor/nerd-fonts || \
		git submodule update --init --checkout vendor/nerd-fonts
	cd vendor/nerd-fonts && \
		git sparse-checkout set --skip-checks font-patcher src/glyphs bin/scripts/name_parser bin/scripts/braille

.PHONY: docker-build
docker-build:
	docker build -t $(IMAGE) .

.PHONY: generate
generate:
	$(DOCKER_RUN) python3 -m robotomonojp generate -c $(CONFIG) -o $(OUTPUT)

.PHONY: generate-regular
generate-regular:
	$(DOCKER_RUN) python3 -m robotomonojp generate -c $(CONFIG) -o $(OUTPUT) --style Regular

.PHONY: print
print:
	$(DOCKER_RUN) python3 -m robotomonojp print $(FONT) "$(TEXT)" -o $(OUT)

.PHONY: reinstall-macos-fonts
reinstall-macos-fonts:
	@set -eu; \
	font_dir="$$HOME/Library/Fonts"; \
	echo "Existing $(FAMILY) fonts in $$font_dir:"; \
	find "$$font_dir" -maxdepth 1 -type f \( -name '$(FAMILY)*.ttf' -o -name '$(FAMILY)*.otf' \) -print | sort; \
	echo; \
	echo "Fonts to install from $(OUTPUT):"; \
	find "$(OUTPUT)" -type f \( -name '*.ttf' -o -name '*.otf' \) -print | sort; \
	echo; \
	printf "Type 'reinstall' to delete existing fonts and install dist fonts: "; \
	read answer; \
	test "$$answer" = "reinstall"; \
	find "$$font_dir" -maxdepth 1 -type f \( -name '$(FAMILY)*.ttf' -o -name '$(FAMILY)*.otf' \) -delete; \
	find "$(OUTPUT)" -type f \( -name '*.ttf' -o -name '*.otf' \) -exec cp {} "$$font_dir"/ \;; \
	if command -v fc-cache >/dev/null 2>&1; then fc-cache -f "$$font_dir" || true; fi; \
	echo "Installed $(FAMILY) fonts:"; \
	find "$$font_dir" -maxdepth 1 -type f \( -name '$(FAMILY)*.ttf' -o -name '$(FAMILY)*.otf' \) -print | sort

.PHONY: lint
lint:
	uvx ruff format --check .
	uvx ruff check .

.PHONY: format
format:
	uvx ruff format .
	uvx ruff check --fix .

.PHONY: test
test:
	uv run --with pydantic --with pyyaml --with typer --with pytest pytest
