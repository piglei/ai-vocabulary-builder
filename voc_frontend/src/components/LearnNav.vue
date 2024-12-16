<script>
export default {
    props: {
        activePanel: {
            type: String,
            required: true
        }
    }
}
</script>

<template>
    <ul class="nav nav-tabs">
        <li class="nav-item">
            <template v-if="activePanel === 'words'">
                <a class="nav-link active">Words</a>
            </template>
            <template v-else>
                <router-link class="nav-link" to="/app/learn">Words</router-link>
            </template>
        </li>
        <li class="nav-item">
            <template v-if="activePanel === 'story'">
                <a class="nav-link active">Story</a>
            </template>
            <template v-else>
                <router-link class="nav-link" to="/app/learn/story">Story</router-link>
            </template>
        </li>
        <li class="nav-item dropdown">
            <template v-if="activePanel === 'more'">
                <a class="nav-link dropdown-toggle active" data-bs-toggle="dropdown" href="#" role="button" aria-expanded="false">More</a>
            </template>
            <template v-else>
                <a class="nav-link dropdown-toggle" data-bs-toggle="dropdown" href="#" role="button" aria-expanded="false">More</a>
            </template>
            <ul class="dropdown-menu">
                <li>
                    <router-link class="nav-link" to="/app/learn/mastered-words">Mastered Words</router-link>
                </li>
            </ul>
        </li>
    </ul>
</template>
