<template>
  <div class="container" style="max-width: 800px">
    <nav class="navbar navbar-expand-sm bg-light mt-2 mb-2">
      <div class="container-fluid">
        <router-link class="navbar-brand" to="/">
          <strong>AI Voc-Builder</strong>
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
              <router-link class="nav-link" to="/manage">Manage</router-link>
            </li>
          </ul>
        </div>
      </div>
    </nav>

    <RouterView />
  </div>
</template>