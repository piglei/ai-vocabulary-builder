.PONY: build-frontend
build-frontend:
	rm -rf voc_builder/notepad/dist
	cd voc_frontend && VITE_AIVOC_API_ENDPOINT='' npm run build-only && mv dist ../voc_builder/notepad

.PONY: build
build: build-frontend
	poetry build
