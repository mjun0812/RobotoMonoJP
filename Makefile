IMAGE ?= robotomonojp:dev
CONFIG ?=
CONFIGS ?= $(sort $(wildcard config/*.yaml))
OUTPUT ?= dist
FAMILY ?= RobotoMonoPlex
JOBS ?= 4

# フォントのインストール先 (macOS / Linux).
ifeq ($(shell uname -s),Darwin)
FONT_DIR ?= $(HOME)/Library/Fonts
else
FONT_DIR ?= $(HOME)/.local/share/fonts
endif

# print のデフォルト. TEXT は 英数字 / ひらがな (濁点・半濁点) / カタカナ / 半角カナ /
# 漢字 / 全角英数・全角記号 / 曖昧幅記号 / Nerd Fonts をsource別 (Pomicons, Powerline,
# FA Extension, Weather, Seti-UI, Devicons, Codicons, Font Awesome, Octicons,
# Font Logos, Material Design, IEC Power) に網羅する.
FONT ?= $(OUTPUT)/$(FAMILY)/$(FAMILY)-Regular.ttf
TEXT ?= AZaz09 あいがぱ アヴパ ｱｲｶﾞﾊﾟ 漢字日本語鬱 Ａ１。、「」￥ ○●■◆★→※±×÷ ⏻           󰀂
OUT ?= preview.pdf
EYECATCH ?= eyecatch.svg
EYECATCH_DIR ?= docs/images
TITLE ?=
DOCKER_RUN = docker run --rm -v $(PWD):/app -w /app $(IMAGE)

.PHONY: help
help:
	@echo "make submodule-init  # Nerd Fonts submoduleを sparse-checkout 込みで初期化"
	@echo "make docker-build    # Dockerイメージをbuild"
	@echo "make generate        # config/*.yaml の全familyの通常版/Mono版を生成"
	@echo "make generate CONFIG=config/{font}.yaml  # 指定familyの通常版/Mono版を生成"
	@echo "make generate-regular  # config/*.yaml の全familyで通常版/Mono版のRegularだけ生成"
	@echo "make install         # dist内の全フォントをインストール (macOS/Linux)"
	@echo "make uninstall       # dist内のfamilyに対応するインストール済みフォントを削除"
	@echo "make reinstall       # uninstall + install"
	@echo "make clean           # distを削除"
	@echo "make print [FONT=... TEXT=... OUT=...]  # フォント確認PDFを生成 (デフォルトで全文字種を網羅)"
	@echo "make preview FONT=...  # 静的HTMLプレビューを tmp/preview.html に生成"
	@echo "make eyecatch        # dist内の全RegularフォントのアイキャッチSVGをdocs/imagesへ生成"
	@echo "make eyecatch FONT=... EYECATCH=...  # 指定フォントだけアイキャッチSVGを生成"
	@echo "make lint            # ruff format --check + ruff check"
	@echo "make typecheck       # ty check"
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
	@set -eu; \
	if [ -n "$(CONFIG)" ]; then \
		$(DOCKER_RUN) python3 -m robotomonojp generate -c "$(CONFIG)" -o "$(OUTPUT)" --jobs "$(JOBS)"; \
	else \
		if [ -z "$(CONFIGS)" ]; then echo "no config files found"; exit 1; fi; \
		printf '%s\n' $(CONFIGS) | xargs -I {} -P "$(JOBS)" sh -c '$(DOCKER_RUN) python3 -m robotomonojp generate -c "$$1" -o "$(OUTPUT)" --jobs 1' sh {}; \
	fi

.PHONY: generate-regular
generate-regular:
	@set -eu; \
	if [ -n "$(CONFIG)" ]; then \
		$(DOCKER_RUN) python3 -m robotomonojp generate -c "$(CONFIG)" -o "$(OUTPUT)" --style Regular; \
	else \
		if [ -z "$(CONFIGS)" ]; then echo "no config files found"; exit 1; fi; \
		printf '%s\n' $(CONFIGS) | xargs -I {} -P "$(JOBS)" sh -c '$(DOCKER_RUN) python3 -m robotomonojp generate -c "$$1" -o "$(OUTPUT)" --style Regular --jobs 1' sh {}; \
	fi

.PHONY: print
print:
	$(DOCKER_RUN) python3 -m robotomonojp print $(FONT) "$(TEXT)" -o $(OUT)

.PHONY: preview
preview:
	uv run robotomonojp preview "$(FONT)" -o tmp/preview.html
	@case "$$(uname -s)" in \
		Darwin) open tmp/preview.html ;; \
		Linux) xdg-open tmp/preview.html ;; \
		*) echo "preview written to tmp/preview.html" ;; \
	esac

.PHONY: eyecatch
eyecatch:
	@set -eu; \
	if [ "$(origin FONT)" != "file" ]; then \
		if [ -n "$(TITLE)" ]; then \
			uv run robotomonojp eyecatch "$(FONT)" -o "$(EYECATCH)" --title "$(TITLE)"; \
		else \
			uv run robotomonojp eyecatch "$(FONT)" -o "$(EYECATCH)"; \
		fi; \
	else \
		fonts=$$(find "$(OUTPUT)" -type f -name '*-Regular.ttf' | sort); \
		if [ -z "$$fonts" ]; then echo "no Regular fonts found in $(OUTPUT)"; exit 1; fi; \
		mkdir -p "$(EYECATCH_DIR)"; \
		for font in $$fonts; do \
			family=$$(basename "$$font" -Regular.ttf); \
			uv run robotomonojp eyecatch "$$font" -o "$(EYECATCH_DIR)/$$family.svg"; \
		done; \
	fi

.PHONY: install
install:
	@set -eu; \
	mkdir -p "$(FONT_DIR)"; \
	echo "Installing fonts from $(OUTPUT) to $(FONT_DIR):"; \
	find "$(OUTPUT)" -type f \( -name '*.ttf' -o -name '*.otf' \) -print | sort; \
	find "$(OUTPUT)" -type f \( -name '*.ttf' -o -name '*.otf' \) -exec cp {} "$(FONT_DIR)"/ \;; \
	if command -v fc-cache >/dev/null 2>&1; then fc-cache -f "$(FONT_DIR)" || true; fi; \
	echo "done"

.PHONY: uninstall
uninstall:
	@set -eu; \
	families=$$(cd "$(OUTPUT)" && ls -d */ 2>/dev/null | tr -d '/'); \
	if [ -z "$$families" ]; then echo "no font families found in $(OUTPUT)"; exit 1; fi; \
	echo "Fonts to remove from $(FONT_DIR):"; \
	for family in $$families; do \
		find "$(FONT_DIR)" -maxdepth 1 -type f \( -name "$$family*.ttf" -o -name "$$family*.otf" \) -print; \
	done | sort; \
	printf "Type 'yes' to remove: "; \
	read answer; \
	test "$$answer" = "yes"; \
	for family in $$families; do \
		find "$(FONT_DIR)" -maxdepth 1 -type f \( -name "$$family*.ttf" -o -name "$$family*.otf" \) -delete; \
	done; \
	if command -v fc-cache >/dev/null 2>&1; then fc-cache -f "$(FONT_DIR)" || true; fi; \
	echo "done"

.PHONY: reinstall
reinstall: uninstall install

.PHONY: clean
clean:
	rm -rf "$(OUTPUT)"

.PHONY: lint
lint:
	uvx ruff format --check .
	uvx ruff check .

.PHONY: typecheck
typecheck:
	uvx ty check

.PHONY: format
format:
	uvx ruff format .
	uvx ruff check --fix .

.PHONY: test
test:
	uv run --with pydantic --with pyyaml --with typer --with pytest pytest
