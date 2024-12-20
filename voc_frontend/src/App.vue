<template>
  <div>
    <nav class="navbar navbar-expand-sm bg-light mb-2">
      <div class="container">
        <router-link class="navbar-brand" id="navbar-brand-logo" to="/">
          <img src="@/images/ai-voc-logo.png" alt="Logo" style="height: 40px; margin-right: 10px;">
          <strong>AI Voc Builder</strong>
        </router-link>
        <button
          class="navbar-toggler"
          type="button"
          data-bs-toggle="collapse"
          data-bs-target="#navbarNav"
          aria-controls="navbarNav"
          aria-expanded="false"
          aria-label="Toggle navigation"
        >
          <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navbarNav">
          <ul class="navbar-nav">
            <li class="nav-item">
              <router-link class="nav-link" to="/">Build</router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/app/learn">Learn</router-link>
            </li>
          </ul>
          <ul class="navbar-nav ms-auto">
            <li class="nav-item">
              <router-link class="nav-link" to="/app/settings">
                <i class="bi bi-gear"></i>
              </router-link>
            </li>
          </ul>
        </div>
      </div>
    </nav>

  <div class="container">
    <RouterView />
  </div>

    <footer class="footer mt-4 py-3 bg-light">
      <div class="container">
        <span class="text-muted">©2024 by <a href="https://www.piglei.com/" target="_blank">@piglei</a>.</span>
        <span class="text-muted float-end">
          <a href="https://github.com/piglei/ai-vocabulary-builder" target="_blank">
            <i class="bi bi-github"></i>
          </a>
        </span>
      </div>
    </footer>

  </div>
</template>

<style lang="scss">
#navbar-brand-logo {
  padding-top: 0;
  padding-bottom: 0;
  display: flex;
  align-items: center;
}
</style>